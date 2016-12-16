"""
@copyright Copyright (c) 2011 - 2016, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file test_lacp_samples.py

@summary   Samples for LACP configuration.

@details
Following test cases are tested:
1. Verify that Dynamic LAG can be created and deleted.
2. Verify that port can be added to(removed from) dynamic LAG.
3. Verify that correct LACP frames are transmitted from the configured dynamic LAG.
"""
import time
from collections import defaultdict

import pytest

from testlib import helpers


@pytest.mark.lacp
@pytest.mark.simplified
class TestLACPSamples(object):
    """
    @description Suite for LACP testing
    """

    def test_configure_dynamic_lag(self, env):
        """
        @brief  Verify that Dynamic LAG can be created and deleted
        @steps
            -# Create dynamic LAG.
            -# Verify dynamic LAG has been created.
            -# Delete dynamic LAG.
            -# Verify dynamic LAG has been deleted.
        @endsteps
        """
        # Create dynamic LAG entry
        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Dynamic', hash_mode='None')

        # Verify that LAG is created.
        lag = {'lagId': 3800,
               'name': 'lag3800',
               'actorAdminLagKey': 0,
               'lagControlType': 'Dynamic',
               'hashMode': 'None'}
        lag_table = env.switch[1].ui.get_table_lags()
        assert lag in lag_table, 'LAG has not been added'

        # Delete created test LAG.
        env.switch[1].ui.delete_lags([3800, ])

        # Verify LAG has been deleted
        lag_table = env.switch[1].ui.get_table_lags()
        assert lag not in lag_table, 'LAG has not been deleted'

    def test_configure_ports_in_dynamic_lag(self, env):
        """
        @brief  Verify that port can be added to(removed from) dynamic LAG
        @steps
            -# Create dynamic LAG.
            -# Add two ports into LAG
            -# Verify ports have been added to LAG.
            -# Delete port from LAG.
            -# Verify port has been deleted from LAG.
        @endsteps
        """
        # Get available DUT ports from the environment
        device_ports = list(env.get_ports([['sw1', 'tg1', 2], ])[('sw1', 'tg1')].values())
        # Create dynamic LAG entry
        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Dynamic', hash_mode='None')

        # Add ports into the LAG
        env.switch[1].ui.create_lag_ports(ports=device_ports, lag=3800, key=0)

        # Verify ports have been added into the LAG
        ports_3800 = [x['portId'] for x in env.switch[1].ui.get_table_ports2lag()
                      if x['lagId'] == 3800]
        assert device_ports[0] in ports_3800, "Port 1 is not a LAG member"
        assert device_ports[1] in ports_3800, "Port 2 is not a LAG member"

        # Delete port 1 from LAG
        env.switch[1].ui.delete_lag_ports(ports=[device_ports[0]], lag=3800)

        # Verify ports in LAG
        ports_3800 = [x['portId'] for x in env.switch[1].ui.get_table_ports2lag()
                      if x['lagId'] == 3800]
        assert device_ports[0] not in ports_3800, "Port 1 is a LAG member"
        assert device_ports[1] in ports_3800, "Port 2 is not a LAG member"

    @pytest.mark.skip("Pypacker does not support LACP protocol")
    def test_lacp_frames(self, env):
        """
        @brief  Verify that correct LACP frames are transmitted from the configured dynamic LAG
        @steps
            -# Add each pair of device ports to separate LAGs
            -# Wait time until LAG transit to defaulted state
            -# Sniff for LACP frames on each LAG port
            -# Verify that device transmits properly formed LACP DUs
        @endsteps
        """
        slow_protocols_mac = "01:80:c2:00:00:02"

        ports = env.get_ports([['tg1', 'sw1', 4], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        dut_mac = env.switch[1].ui.get_table_bridge_info(param="macAddress")
        sysprio = env.switch[1].ui.get_table_link_aggregation()[0]["priority"]
        max_delay = env.switch[1].ui.get_table_link_aggregation()[0]["collectorMaxDelay"]
        lacp_ethertype = 0x8809

        # Configure LAGs
        lag_config = {ports[("sw1", "tg1")][1]: {'key': 0, 'portprio': 4096},
                      ports[("sw1", "tg1")][2]: {'key': 0, 'portprio': 4096},
                      ports[("sw1", "tg1")][3]: {'key': 1, 'portprio': 8192},
                      ports[("sw1", "tg1")][4]: {'key': 1, 'portprio': 8192}}

        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Dynamic', hash_mode='None')
        env.switch[1].ui.create_lag_ports(ports=[ports[("sw1", "tg1")][1],
                                                 ports[("sw1", "tg1")][2]],
                                          lag=3800,
                                          priority=4096,
                                          lag_mode='Active',
                                          key=0,
                                          timeout='Short')

        env.switch[1].ui.create_lag(lag=3801, key=1, lag_type='Dynamic', hash_mode='None')
        env.switch[1].ui.create_lag_ports(ports=[ports[("sw1", "tg1")][3],
                                                 ports[("sw1", "tg1")][4]],
                                          lag=3801,
                                          priority=8192,
                                          lag_mode='Active',
                                          key=1,
                                          timeout='Short')

        self.suite_logger.debug("Wait time to transit to defaulted state")
        time.sleep(5)

        sniff_tg_ports = list(ports[("tg1", "sw1")].values())

        env.tg[1].start_sniff(sniff_tg_ports,
                              sniffing_time=30,
                              dst_filter=slow_protocols_mac)

        self.suite_logger.debug("Get Actor and Partner operStates.")
        states = defaultdict(dict)
        states[ports[("sw1", "tg1")][1]]['actor'] = [x for x in env.switch[1].ui.get_table_lags_local_ports(lag=3800)
                                                     if x['portId'] == ports[("sw1", "tg1")][1]][0]['actorOperPortState']
        states[ports[("sw1", "tg1")][1]]['partner'] = [x for x in env.switch[1].ui.get_table_lags_remote_ports(lag=3800)
                                                       if x['portId'] == ports[("sw1", "tg1")][1]][0]['partnerOperPortState']
        states[ports[("sw1", "tg1")][2]]['actor'] = [x for x in env.switch[1].ui.get_table_lags_local_ports(lag=3800)
                                                     if x['portId'] == ports[("sw1", "tg1")][2]][0]['actorOperPortState']
        states[ports[("sw1", "tg1")][2]]['partner'] = [x for x in env.switch[1].ui.get_table_lags_remote_ports(lag=3800)
                                                       if x['portId'] == ports[("sw1", "tg1")][2]][0]['partnerOperPortState']
        states[ports[("sw1", "tg1")][3]]['actor'] = [x for x in env.switch[1].ui.get_table_lags_local_ports(lag=3801)
                                                     if x['portId'] == ports[("sw1", "tg1")][3]][0]['actorOperPortState']
        states[ports[("sw1", "tg1")][3]]['partner'] = [x for x in env.switch[1].ui.get_table_lags_remote_ports(lag=3801)
                                                       if x['portId'] == ports[("sw1", "tg1")][3]][0]['partnerOperPortState']
        states[ports[("sw1", "tg1")][4]]['actor'] = [x for x in env.switch[1].ui.get_table_lags_local_ports(lag=3801)
                                                     if x['portId'] == ports[("sw1", "tg1")][4]][0]['actorOperPortState']
        states[ports[("sw1", "tg1")][4]]['partner'] = [x for x in env.switch[1].ui.get_table_lags_remote_ports(lag=3801)
                                                       if x['portId'] == ports[("sw1", "tg1")][4]][0]['partnerOperPortState']

        data = env.tg[1].stop_sniff(sniff_tg_ports)

        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify that correct LACP frames are sent from each LAG port.")
        for index in range(1, 5):
            tg_port = ports[("tg1", "sw1")][index]
            sw_port = ports[("sw1", "tg1")][index]
            try:
                assert data[tg_port], "No LACP frames sniffed on %s port".format(tg_port)
            except KeyError:
                pytest.fail("No LACP frame sniffed on %s port" % tg_port)
            for lacp_frame in data[tg_port]:
                prt_state = [int(bit_val) for bit_val in states[sw_port]["partner"]]
                partner_tlv = {"type": 2, "length": 20, "sysprio": 32768,
                               "sys": "00:00:00:00:00:00",
                               "key": 0, "portprio": 32768, "port": 1,
                               "expired": prt_state[0], "defaulted": prt_state[1],
                               "distribute": prt_state[2], "collect": prt_state[3],
                               "synch": prt_state[4], "aggregate": prt_state[5],
                               "timeout": prt_state[6], "activity": prt_state[7],
                               "reserved": "\x00" * 3}

                act_state = [int(bit_val) for bit_val in states[sw_port]["actor"]]
                expected_layers = {"Ethernet": {"src": dut_mac,
                                             "type": lacp_ethertype},
                                   "LACP": {"version": 1,
                                            "subtype": 1},
                                   "LACPActorInfoTlv": {"type": 1,
                                                        "length": 20,
                                                        "sysprio": sysprio,
                                                        "sys": dut_mac,
                                                        "key": lag_config[sw_port]['key'],
                                                        "portprio": lag_config[sw_port]["portprio"],
                                                        "port": sw_port,
                                                        "expired": act_state[0],
                                                        "defaulted": act_state[1],
                                                        "distribute": act_state[2],
                                                        "collect": act_state[3],
                                                        "synch": act_state[4],
                                                        "aggregate": act_state[5],
                                                        "timeout": act_state[6],
                                                        "activity": act_state[7],
                                                        "reserved": "\x00" * 3},
                                   "LACPPartnerInfoTlv": partner_tlv,
                                   "LACPCollectorInfoTlv": {"type": 3,
                                                            "length": 16,
                                                            "maxdelay": max_delay,
                                                            "reserved": "\x00" * 12},
                                   "LACPTerminatorTlv": {"type": 0,
                                                         "length": 0},
                                   "LACPReserved": {"reserved": "\x00" * 50}}
                failures = []
                for layer in expected_layers:
                    for field, expected_value in expected_layers[layer].items():
                        pack_value = env.tg[1].get_packet_field(lacp_frame, layer, field)
                        try:
                            if isinstance(pack_value, str):
                                assert pack_value.lower() == expected_value.lower(), \
                                    "Incorrect {} field {} value transmitted in LACP frame: {}".format(layer[4:], field, pack_value)
                            else:
                                assert pack_value == expected_value, "Incorrect {} field {} value transmitted in LACP frame: {}".format(layer[4:], field, pack_value)
                        except AssertionError as err:
                            failures.append("%s" % err)

                if failures:
                    pytest.fail("\n".join(failures))
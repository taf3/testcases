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

@file test_lag_samples.py

@summary   Samples for LAG configuration.

@details
Following test cases are tested:
1. Verify that static LAG can be created and deleted.
2. Verify that port can be added to(removed from) static LAG.
3. Verify that traffic is processed according to the configured LAGs.
"""

import pytest

from testlib import helpers


@pytest.mark.lag
@pytest.mark.simplified
class TestLagSamples(object):
    """
    @description Suite for LAG testing
    """

    def test_configure_static_lag(self, env):
        """
        @brief  Verify that static LAG can be created and deleted
        @steps
            -# Create static LAG.
            -# Verify static LAG has been created.
            -# Delete static LAG.
            -# Verify static LAG has been deleted.
        @endsteps
        """
        # Create static LAG entry
        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Static', hash_mode='None')

        # Verify that LAG is created.
        lag = {'lagId': 3800,
               'name': 'lag3800',
               'actorAdminLagKey': 0,
               'lagControlType': 'Static',
               'hashMode': 'None'}
        lag_table = env.switch[1].ui.get_table_lags()
        assert lag in lag_table, 'LAG has not been added'

        # Delete created test LAG.
        env.switch[1].ui.delete_lags([3800, ])

        # Verify LAG has been deleted
        lag_table = env.switch[1].ui.get_table_lags()
        assert lag not in lag_table, 'LAG has not been deleted'

    def test_configure_ports_in_lag(self, env):
        """
        @brief  Verify that port can be added to(removed from) static LAG
        @steps
            -# Create static LAG.
            -# Add two ports into LAG
            -# Verify ports have been added to LAG.
            -# Delete port from LAG.
            -# Verify port has been deleted from LAG.
        @endsteps
        """
        # Get available DUT ports from the environment
        device_ports = list(env.get_ports([['sw1', 'tg1', 2], ])[('sw1', 'tg1')].values())
        # Create static LAG entry
        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Static', hash_mode='None')

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

    def test_lag_traffic(self, env):
        """
        @brief  Verify that port can be added to(removed from) static LAG
        @steps
            -# Create static LAG.
            -# Add two ports into LAG
            -# Send traffic to the first LAG member.
            -# Verify traffic is forwarded only from non-LAG members.
        @endsteps
        """
        # Get active ports: use four ports for test case
        active_ports = env.get_ports([['tg1', 'sw1', 3], ])
        device_ports = list(active_ports[('sw1', 'tg1')].values())
        sniff_ports = list(active_ports[('tg1', 'sw1')].values())

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)

        # Disable STP globally in order to avoid traffic loop
        env.switch[1].ui.configure_spanning_tree(enable="Disabled")

        helpers.set_ports_admin_enabled(env.switch, active_ports)

        # Create static LAG entry
        env.switch[1].ui.create_lag(lag=3800, key=0, lag_type='Static', hash_mode='None')

        # Add port into the LAG
        env.switch[1].ui.create_lag_ports(ports=device_ports[:2],
                                          lag=3800, key=0)

        env.switch[1].ui.wait_for_port_value_to_change(
            ports=[3800] + device_ports[:2], port_parameter='operationalStatus', value='Up')

        # Generate test traffic
        packet = ({"Ethernet": {"dst": "00:00:11:11:11:11", "src": "00:00:02:02:02:02"}},
                  {"IP": {}}, {"TCP": {}})

        # Send packets to the first port
        stream = env.tg[1].set_stream(packet, count=1, iface=sniff_ports[0])

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        # Get packets from the captured data
        # Verify first packet is sent only to second port
        params = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:11:11:11:11'},
                  {"layer": "Ethernet", "field": 'src', "value": '00:00:02:02:02:02'}]

        #Traffic should be forwarded from non-LAG members
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

        # Traffic should not be forwarded from LAG members
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"

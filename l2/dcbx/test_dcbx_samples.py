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

@file test_dcbx_samples.py

@summary   Samples for DCBX configuration.

@details
Following test cases are tested:
1. Verify that the DUT inhibits the transmission of max_sized frames when a PFC frame
   is received with quanta value equal to 10000.
"""
import time

import pytest

from testlib import helpers


def pytest_generate_tests(metafunc):
    """Py.test hook that generates test items based on type of PFC configuration on device"""
    try:
        type_of_pfc_config = metafunc.config.env.switch[1].hw.SUPPORTED_PFC_CONFIGURATION.PFC_TYPE_CONFIGURATION
    except KeyError:
        type_of_pfc_config = None
    if type_of_pfc_config == 1:
        argvalue = ['Dcbx']
    elif type_of_pfc_config == 2:
        argvalue = ['Manual']
    elif type_of_pfc_config == 3:
        argvalue = ['Dcbx', 'Manual']
    else:
        argvalue = [helpers.skiptest("Manual and DCBX types of PFC configuration are not support on device")('Not_supported')]
    metafunc.parametrize('type_of_pfc_config', argvalue)


@pytest.mark.dcbx
@pytest.mark.simplified
class TestDCBXSamples(object):
    """
    @description Suite for DCBX testing
    """

    # Attributest and Properties

    def configure_dcbx_pfc(self, switch_inst, tg_inst, ports):
        """
        @brief  Make proper PFC configuration by setting DcbxPfcPortsAdmin values and sending DCBX PFC frames
        @param switch_inst:  switch instance
        @type  switch_inst:  SwitchGeneral
        @param tg_inst:  traffic generator instance
        @type  tg_inst:  GenericTG
        @param ports:  active ports for specific environment
        @type  ports:  dict{dict}
        @ raise  AssertionError:  DCBx PFC configuration is not set to DcbxPfcPortsLocal
        """
        switch_inst.ui.enable_dcbx_tlv_transmission(list(ports[("sw1", "tg1")].values()),
                                                    dcbx_tlvs=["tlvPfcTxEnable"],
                                                    mode="Enabled")
        self.suite_logger.debug("Configure all ports to accept PFC DCBX tlvs configurations")
        switch_inst.ui.configure_dcbx_pfc(list(ports[("sw1", "tg1")].values()),
                                          willing='Enabled')

        self.suite_logger.debug("Send DCBX frame in order to make proper PFC configuration to all ports")
        dcbx_stream = []
        for link in ports[("sw1", "tg1")]:
            dcbx_pfc_packet = self.build_dcbx_frame("po%02x" % link,
                                                    "00:00:00:01:02:%02x" % link)
            dcbx_stream.append(tg_inst.set_stream(dcbx_pfc_packet,
                                                  count=1,
                                                  iface=ports[("tg1", "sw1")][link]))
        tg_inst.start_streams(dcbx_stream)
        time.sleep(0.5)
        tg_inst.stop_streams(dcbx_stream)
        self.suite_logger.debug("Wait time to update PFC configuration in DcbxPfcPortsLocal table")
        time.sleep(2)

        self.suite_logger.debug("Verify that PFC configuration is set in DcbxPfcPortsLocal table for egress port")
        for port in ports[("sw1", "tg1")].values():
            assert switch_inst.ui.get_table_dcbx_pfc(table_type="Local",
                                                     port=port)[0]["enabled"] == '0,1,0,0,0,0,0,0', \
                "DCBx PFC configuration is not set to DcbxPfcPortsLocal"

    def configure_pfc_manually_without_frame_sending(self, switch_inst, ports, traffic_class):
        """
        @brief  Make proper PFC configuration manually without sending DCBX PFC frames
        @param switch_inst:  switch instance
        @type  switch_inst:  SwitchGeneral
        @param ports:  active ports for specific switch instance
        @type  ports:  list(int)
        @param traffic_class:  traffic class
        @type  traffic_class:  int
        """
        switch_inst.ui.set_flow_control_type(ports, control_type='Rx', tc=[traffic_class])

    def build_dcbx_frame(self, port_name, src_mac):
        """
        @brief  Build lldpdu dcbx frame according to transmitted values: port_name, src_mac, pfc_data
        @param port_name:  interface name
        @type  port_name:  str
        @param src_mac:  Source MAC address
        @type  src_mac:  str
        @rtype:  list(dict)
        @return:  DCBx packet definition
        """
        dcbx_packet = ({"Ethernet": {"dst": '01:80:c2:00:00:0e',
                                  "src": src_mac,
                                  "type": 0x88cc}},
                       {"LLDP": {"tlvlist": [{"LLDPChassisId": {"type": 1,
                                                                "subtype": "MAC address",
                                                                "macaddr": src_mac}},
                                             {"LLDPPortId": {"type": 2,
                                                             "subtype": "Interface alias",
                                                             "value": port_name}},
                                             {"LLDPTTL": {"type": 3,
                                                          "seconds": 300}},
                                             {"LLDPPortDescription": {"type": 4,
                                                                      "value": "port_desc_%s" % port_name}},
                                             {"LLDPSystemName": {"type": 5,
                                                                 "value": '<sys-name>'}},
                                             {"LLDPSystemDescription": {"type": 6,
                                                                        "value": '<sys-desc>'}},
                                             {"LLDPSystemCapabilities": {"type": 7,
                                                                         "capabilities": "bridge",
                                                                         "enabled": "bridge"}},
                                             {"DCBXConfiguration": {"type": 127,
                                                                    "length": 25,
                                                                    "oui": 0x80c2,
                                                                    "subtype": "ETS Configuration",
                                                                    "willing": 0,
                                                                    "cbs": 0,
                                                                    "reserved": 0,
                                                                    "maxtcs": 0,
                                                                    "priority": [0, 1, 2, 3, 4, 5, 6, 7],
                                                                    "tcbandwith": [10, 10, 10, 10, 10, 10, 10, 30],
                                                                    "tsaassigment": [2, 2, 2, 2, 2, 2, 2, 2]}},
                                             {"DCBXPriorityBasedFlowControlConfiguration": {"type": 127,
                                                                                            "length": 6,
                                                                                            "oui": 0x80c2,
                                                                                            "subtype": "Priority-based Flow Control Configuration",
                                                                                            "willing": 0,
                                                                                            "mbc": 1,
                                                                                            "reserved": 0,
                                                                                            "pfccap": 1,
                                                                                            "pfcenable": [0, 0, 0, 0, 0, 0, 1, 0]}},
                                             {"LLDPDUEnd": {"type": 0,
                                                            "length": 0}}]}})
        return dcbx_packet

    def build_pause_frame(self, src_mac=None):
        """
        @brief  Build pause frame according to transmitted values: src_mac, priority_vector, time_quanta
        @param src_mac:  Source MAC address
        @type  src_mac:  str
        @rtype:  list(dict)
        @return:  PFC packet definition
        """
        return ({'Ether': {'dst': '01:80:c2:00:00:01',
                           'src': src_mac,
                           'type': 0x8808}},
                {'Pause': {'opcode': 0x0101,
                           'ls': [0, 0, 0, 0, 0, 0, 1, 0],
                           'timelist': [0, 1000, 0, 0, 0, 0, 0, 0]}})

    def get_packets_count_in_traffic_rate(self, tg_inst, tg_port, frame, rate=100, size=64):
        """
        @brief  Return the number of frames transmitted per second according to defined traffic rate
        @param tg_inst:  traffic generator instance
        @type  tg_inst:  GenericTG
        @param tg_port:  traffic generator's interface
        @type  tg_port:  tuple|str
        @param frame:  packet definition
        @type  frame:  list(dict)
        @param rate:  traffic rate in percentages
        @type  rate:  int
        @param size:  packet size
        @type  size:  int
        @rtype:  int
        @return:  Tx frames_per_second rate
        """
        stream = tg_inst.set_stream(frame,
                                    iface=tg_port,
                                    continuous=True,
                                    rate=rate,
                                    required_size=size)
        tg_inst.start_sniff([tg_port, ])
        tg_inst.start_streams([stream, ])
        time.sleep(3)
        traffic_rate = tg_inst.get_port_txrate(tg_port)
        tg_inst.stop_sniff([tg_port, ], drop_packets=True)
        tg_inst.stop_streams([stream, ])

        return traffic_rate

    def get_pause_frames_rate_to_halt_traffic(self, quanta, port_speed, decrease_rate, max_pause_frame_rate=14880952):
        """
        @brief  Return the number of pause frames required to decrease the rate of traffic
        @param quanta:  PFC quanta
        @type  quanta:  int
        @param port_speed:  switch port speed
        @type  port_speed:  int
        @param decrease_rate:  expected decrease rate in percentages
        @type  decrease_rate:  int
        @param max_pause_frame_rate:  traffic frames_per_second rate
        @type  max_pause_frame_rate:  int
        @rtype:  int
        @return:  PFC frames rate
        """
        port_speed = 1000 * 1000 * port_speed
        pause_frame_count = (port_speed * decrease_rate / 100.) / (quanta * 512)
        return round(pause_frame_count * 100 / max_pause_frame_rate, 5)

    # Test Cases
    @pytest.mark.skip("Pypacker does not support LLDP protocol")
    def test_pfc_inhibit_traffic_of_max_sized_frames(self, env, type_of_pfc_config):
        """
        @brief  Verify that the DUT inhibits the transmission of max_sized frames when a PFC frame is received with quanta value equal to 1000.
        @steps
        -# Connect device with TG
        -# Configure egress port to accept PFC configurations
        -# Send DCBX PFC tlv to egress port: pfc enabled for 1 priority
        -# Configure Dot1p PortsQoS trust mode on ingress ports
        -# Create Static MAC entry to redirect traffic to egress port
        -# Transmit priority 1 traffic of max_sized frames from ingress ports
        -# Transmit pause frames with quanta value 1000 for 1 priority to egress port
        -# Verify that traffic rate is decreased according to sent pause frames
        @endsteps
        """
        decrease_rate = 40

        ports = env.get_ports([['tg1', 'sw1', 3], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        env.switch[1].ui.create_vlans([20, ])
        env.switch[1].ui.create_vlan_ports(iter(ports[('sw1', 'tg1')].values()), [20], 'Tagged')

        egress_link = ports[('sw1', 'tg1')][1]
        egress_tg_port = ports[("tg1", "sw1")][1]
        ingress_tg_ports = [ports[("tg1", "sw1")][2], ports[("tg1", "sw1")][3]]

        # Create StaticMac
        env.switch[1].ui.create_static_macs(ports[('sw1', 'tg1')][1], [20, ], ['00:00:02:02:02:02', ])

        if type_of_pfc_config == 'Dcbx':
            self.configure_dcbx_pfc(env.switch[1], env.tg[1], ports)
        elif type_of_pfc_config == 'Manual':
            self.configure_pfc_manually_without_frame_sending(env.switch[1],
                                                              iter(ports[('sw1', 'tg1')].values()), 1)

        pause_frame = self.build_pause_frame(src_mac='00:00:02:02:02:02')
        max_pause_frame_rate = self.get_packets_count_in_traffic_rate(env.tg[1],
                                                                      egress_tg_port,
                                                                      pause_frame,
                                                                      rate=100, size=64)

        # define priority tagged traffic to transmit through egress port
        streams = []
        tgport_prio_dict = {}
        iter_ingress_ports = iter(ingress_tg_ports)

        packet = ({"Ethernet": {"src": "00:11:11:11:11:12", "dst": '00:00:02:02:02:02'}},
                  {"Dot1Q": {"prio": 1, "type": 0x0800, "vlan": 20}},
                  {"IP": {}}, {"UDP": {}})

        for tg_port in iter_ingress_ports:
            streams.append(env.tg[1].set_stream(packet,
                                                iface=tg_port,
                                                continuous=True,
                                                rate=100,
                                                required_size=1518))
            tgport_prio_dict[tg_port] = 1

        env.tg[1].start_streams(streams)

        # Wait time to get sustainable traffic rate value
        time.sleep(2)
        initial_traffic_rate = env.tg[1].get_port_rxrate(egress_tg_port)
        env.tg[1].stop_streams()
        env.tg[1].clear_statistics(ingress_tg_ports + [egress_tg_port])

        env.tg[1].set_qos_stat_type(egress_tg_port, "VLAN")

        self.suite_logger.debug("Start sending Pause frames to egress port")
        port_speed = env.switch[1].ui.get_table_ports(ports=[egress_link, ],
                                                      all_params=True)[0]["speed"]

        pause_frame_rate = self.get_pause_frames_rate_to_halt_traffic(quanta=1000,
                                                                      port_speed=port_speed,
                                                                      decrease_rate=decrease_rate,
                                                                      max_pause_frame_rate=max_pause_frame_rate)
        pause_stream = env.tg[1].set_stream(pause_frame,
                                            iface=egress_tg_port,
                                            continuous=True,
                                            rate=pause_frame_rate)
        env.tg[1].start_sniff([egress_tg_port, ])
        env.tg[1].start_streams([pause_stream, ] + streams)
        time.sleep(2)

        self.suite_logger.debug("Check port rate after transmitting pause frames")
        delay_rates = []
        end_time = time.time() + 15
        while time.time() <= end_time:
            # Check port rate each 5 seconds after transmitting pause frames
            actual_traffic_rate = env.tg[1].get_port_rxrate(egress_tg_port)
            delay_rates.append({"actual_rate": actual_traffic_rate,
                                "delay_rate": (initial_traffic_rate - actual_traffic_rate) * 100. / initial_traffic_rate})
            time.sleep(5)

        env.tg[1].stop_sniff([egress_tg_port, ], drop_packets=True)
        env.tg[1].stop_streams()

        self.suite_logger.debug("Verify that traffic rate is decreased according to sent pause frames")
        for rate in delay_rates:
            assert abs(rate["delay_rate"] - decrease_rate) <= 3, "Traffic rate is not decreased according to sent pause frames"

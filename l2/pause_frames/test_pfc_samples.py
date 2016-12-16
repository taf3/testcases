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

@file test_pfc_samples.py

@summary   Samples for PFC configuration.

@details
Following test cases are tested:
1. Verify that device doesn't flood received pause frames when flow control
    mode is configured.
2. Verify that "RxTx" flow control manages traffic correctly.
"""
import time

import pytest

from testlib import helpers


@pytest.mark.flow_control
@pytest.mark.simplified
class TestPFCSamples(object):
    """
    @description Suite for PFC testing
    """

# Attributes and Properties

    def rate_decreasing(self, pf_rate=None, quanta=None, pause_frame_size=64,
                        full_rate=None, actual_rate=None):
        """
        @brief Calculated expected line rate during stream of pause frames is sending.
        @param pf_rate:  PFC rate
        @type  pf_rate:  int
        @param quanta:  PFC quanta
        @type  quanta:  int
        @param pause_frame_size:  PFC frame size
        @type  pause_frame_size:  int
        @param full_rate:  full rate
        @type  full_rate:  int
        @param actual_rate:  actual rate
        @type  actual_rate:  int
        @rtype:  bool
        @return:  True if actual rate is equal to the calculated expected line rate
        """
        x = pf_rate // 10
        ptime = quanta * 96
        frame_rate = (x * 1000000000) // (pause_frame_size + 20) // 8
        sweeper_p = frame_rate * ptime
        delay_sent = (sweeper_p * 100.) / 1000000000
        delay_received = 100 - delay_sent
        expected_rate = (full_rate * delay_received) / 100
        if expected_rate <= 0:
            expected_rate = 0
            if not actual_rate - expected_rate == 0:
                return False
            else:
                return True
        else:
            if abs(actual_rate - expected_rate) <= 10:
                return True
            else:
                return False

    def full_rate(self, sw_instance=None, tested_port=None, frame_size=None):
        """
        @brief Calculation of full line rate for tested ports.
        @param sw_instance:  switch instance
        @type  sw_instance:  SwitchGeneral
        @param tested_port:  switch port ID
        @type  tested_port:  int
        @param frame_size:  frame size
        @type  frame_size:  int
        @rtype:  int
        @return:  full line rate
        """
        speed_value = sw_instance.ui.get_table_ports([tested_port], True)[0]['speed']
        full_line_rate = (speed_value * 1000000.) / ((frame_size + 20) / 8)
        return full_line_rate

# Test Cases
    @pytest.mark.skip("Pypacker does not support Pause frames")
    def test_sent_pause_frames(self, env):
        """
        @brief  Verify that device doesn't flood received pause frames when flow control mode is configured.
        @steps
            -# Configure FlowControl on switch ports.
            -# Send PFC frames to the switch.
            -# Verify PFC frames are not flooded.
        @endsteps
        """
        # Define active ports
        ports = env.get_ports([['tg1', 'sw1', 3], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Wait until ports will be in forwarding state.
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][1],
                                              timeout=120)
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][2],
                                              timeout=120)
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][3],
                                              timeout=120)

        # Configure stream of pause frame.
        pause_frame = ({"Ethernet": {"dst": "01:80:C2:00:00:01",
                                  "src": "00:00:00:00:01:44",
                                  "type": 0x8808}},
                       {"Pause": {"opcode": 0x0001, "ptime": 1}})
        stream = env.tg[1].set_stream(pause_frame,
                                      count=10,
                                      iface=ports[('tg1', 'sw1')][1])

        sniff_ports = list(ports[('tg1', 'sw1')].values())

        # Configure flow control values for all active ports.
        env.switch[1].ui.set_flow_control_type([ports[('sw1', 'tg1')][1],
                                                ports[('sw1', 'tg1')][2],
                                                ports[('sw1', 'tg1')][3]],
                                               control_type='RxTx')

        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)
        # Send pause frame from the TG port 1.
        env.tg[1].send_stream(stream)

        data = env.tg[1].stop_sniff(sniff_ports)
        helpers.print_sniffed_data_brief(data)
        # Verify that Pause Frames are not forwarded from tested ports.
        params = ({'layer': "Ethernet",
                   'field': "dst",
                   'value': "01:80:C2:00:00:01".lower()}, )
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 1 when PF traffic is sent"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 2 when PF traffic is sent"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 3 when PF traffic is sent"

    @pytest.mark.skip("Pypacker does not support Pause frames")
    def test_rxtx_flow_control(self, env):
        """
        @brief Verify that "RxTx" flow control manages traffic correctly.
        @steps
            -# Configure FlowControl on switch ports in 'RxTx' mode.
            -# Send stream of unicast packets with 50% rate to the port 1.
            -# Send stream of unicast packets with 50% rate to the port 2.
            -# Send PFC frames to the port 3.
            -# Verify that line rate on TG port 3 decreases after pause frames with middle quanta are sending
        @endsteps
        """
        self.suite_logger.info("Define variables for test execution")
        pause_frame_rate = 30
        quanta_value = 4096

        # Define active ports
        ports = env.get_ports([['tg1', 'sw1', 3], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Wait until ports will be in forwarding state.
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][1],
                                              timeout=120)
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][2],
                                              timeout=120)
        helpers.wait_until_stp_state(switch_instance=env.switch[1], mode="RSTP",
                                              state="Forwarding",
                                              port=ports[('sw1', 'tg1')][3],
                                              timeout=120)

        # Configure two streams of unicast packets.
        packet_1 = ({"Ethernet": {"dst": "00:00:00:00:00:33",
                               "src": "00:00:00:00:00:11",
                               "type": 0x0800}},
                    {"IP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:00:00:33",
                               "src": "00:00:00:00:00:22",
                               "type": 0x0800}},
                    {"IP": {}})
        stream_1 = env.tg[1].set_stream(packet_1,
                                        iface=ports[('tg1', 'sw1')][1],
                                        rate=50,
                                        continuous=True)
        stream_2 = env.tg[1].set_stream(packet_2,
                                        iface=ports[('tg1', 'sw1')][2],
                                        rate=50,
                                        continuous=True)

        sniff_ports = list(ports[('tg1', 'sw1')].values())

        # Configure flow control values for all active ports.
        env.switch[1].ui.set_flow_control_type([ports[('sw1', 'tg1')][1],
                                                ports[('sw1', 'tg1')][2],
                                                ports[('sw1', 'tg1')][3]],
                                               control_type='RxTx')

        # Enable Flow Control on TG port 1 and port 2
        env.tg[1].set_flow_control(ports[('tg1', 'sw1')][1], True)
        env.tg[1].set_flow_control(ports[('tg1', 'sw1')][2], True)

        # Send stream of unicast packets from TG port 1.
        env.tg[1].start_streams([stream_1, stream_2, ])
        time.sleep(3)

        # Configure stream of pause frames
        pause_frame = ({"Ethernet": {"dst": "01:80:C2:00:00:01",
                                  "src": "00:00:00:00:01:44",
                                  "type": 0x8808}},
                       {"Pause": {"opcode": 0x0001,
                                  "ptime": quanta_value}})
        stream = env.tg[1].set_stream(pause_frame,
                                      iface=ports[('tg1', 'sw1')][3],
                                      rate=pause_frame_rate,
                                      continuous=True)

        # Send stream of pause frames from TG port 2.
        env.tg[1].start_streams([stream, ])
        time.sleep(3)

        self.suite_logger.debug("Start sniffer for detecting pause frames")
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5, filter_layer='PAUSE')
        time.sleep(5)

        # Define transmit rate limits on TG port 1 and port 2 after sending pause frames to "RxTx" flow control port.
        tx_test_rate1 = env.tg[1].get_port_txrate(ports[('tg1', 'sw1')][1])
        tx_test_rate2 = env.tg[1].get_port_txrate(ports[('tg1', 'sw1')][2])
        # Define receive rate limit on TG port 3 after sending pause frames to "RxTx" flow control port.
        rx_test_rate3 = env.tg[1].get_port_rxrate(ports[('tg1', 'sw1')][3])

        self.suite_logger.debug("Stop sniffer")
        data = env.tg[1].stop_sniff(sniff_ports)
        # Stop streams of unicast packets and pause frames.
        env.tg[1].stop_streams([stream_1, stream_2, stream, ])

        # Verify that pause frames are not forwarded from tested ports.
        params = ({'layer': "Ethernet", 'field': "src", 'value': "00:00:00:00:01:44"}, )
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 1 when 'RxTx' is configured on all tested ports."
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 2 when 'RxTx' is configured on all tested ports."
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Pause Frames are forwarded from port 3 when 'RxTx' is configured on all tested ports."

        # Verify that line rate on TG port 3 decreases after pause frames with middle quanta are sending.
        if self.rate_decreasing(pf_rate=pause_frame_rate,
                                quanta=quanta_value,
                                pause_frame_size=64,
                                full_rate=self.full_rate(sw_instance=env.switch[1],
                                                         tested_port=ports[('sw1', 'tg1')][3],
                                                         frame_size=64),
                                actual_rate=rx_test_rate3):
            self.suite_logger.debug("Line rate decreases properly when stream of pause frames with middle quanta is sent to 'RxTx' port.")
        else:
            pytest.fail("Line rate is not decreased properly when stream of pause frames with middle quanta is sent to 'RxTx' port.")

        # Verify that transmit line rate on TG port 1 is decreased according to configured "RxTx" flow control on all tested ports.
        if not abs(tx_test_rate1 - (rx_test_rate3 // 2)) <= rx_test_rate3 // 2 * 101 // 100:
            pytest.fail("Transmit line rate is not decreased accordingly to detected overflow on 'RxTx' egress port.")

        # Verify that transmit line rate on TG port 2 is decreased according to configured "RxTx" flow control on all tested ports.
        if not abs(tx_test_rate2 - (rx_test_rate3 // 2)) <= rx_test_rate3 / 2 * 101 // 100:
            pytest.fail("Transmit line rate is not decreased accordingly to detected overflow on 'RxTx' egress port.")

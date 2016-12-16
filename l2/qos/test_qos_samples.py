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

@file test_qos_samples.py

@summary   Samples for QoS configuration.

@details
Following test cases are tested:
1. Verify that packets with Dot1p higher priority displace packets with Dot1p lower priority by Strict schedule mode
2. Verify that packets with DSCP higher priority displace packets with DSCP lower priority by Strict schedule mode


"""
import time

import pytest

from testlib import helpers


@pytest.mark.qos
@pytest.mark.simplified
class TestQoSSamples(object):
    """
    @description Suite for QoS testing
    """

# Attributes and Properties

    def not_used_cos_statistics(self, tg_instance=None, prio_value_1=None,
                                prio_value_2=None, iface=None):
        """
        @brief Function for checking that packets not used in test are
               not sniffed on target interface.

        @param  tg_instance:  TG instance
        @type tg_instance: Tg | GenericTg
        @param  prio_value_1:  Priority value used in test case
        @type prio_value_1: int
        @param  prio_value_2:  Priority value used in test case
        @type prio_value_2: int
        @param  iface:  Sniffed interface
        @type iface: tuple

        @return True if there is no unused sniffed packets
                False if unused packets are present.
        @rtype: bool

        """
        unused_cos_set = set(range(1, 8)) - {prio_value_1, prio_value_2}
        unused_cos_stats = (tg_instance.get_qos_frames_count(iface, n)
                            for n in unused_cos_set)
        return all(c == 0 for c in unused_cos_stats)

# Test Cases
    @pytest.mark.skip("Pypacker does not support Vlan prio field")
    def test_qos_dot1q_strict_mode(self, env):
        """
        @brief  Verify that packets with Dot1p higher priority displace packets
                with Dot1p lower priority by Strict schedule mode
        @steps
            -# Set Dot1p trust mode value on ingress port 1 and port 2.
            -# Set Strict sched mode value on egress port 3.
            -# Send two streams with different Dot1p priorities.
            -# Verify that packets with Dot1p higher priority displace packets with Dot1p lower priority
        @endsteps
        """
        prio_higher = 6
        prio_lower = 4

        src_1 = "00:00:00:00:01:11"
        src_2 = "00:00:00:00:02:22"
        dst_3 = "00:00:00:00:03:33"

         # Define active ports
        ports = env.get_ports([['sw1', 'tg1', 3], ])

        device_ports = list(ports[('sw1', 'tg1')].values())

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Disable Flow Control functionality
        env.switch[1].ui.modify_ports(device_ports, flowControl='None')
        for port in device_ports:
            env.switch[1].ui.wait_for_port_status(port, 'flowControl', 'None', 10)

        # Disable Cut Through functionality
        env.switch[1].ui.modify_ports(device_ports, cutThrough='Disabled')
        for port in device_ports:
            env.switch[1].ui.wait_for_port_status(port, 'cutThrough', 'Disabled', 10)

        # SetUp multicast and broadcast rate limits
        env.switch[1].ui.modify_ports(device_ports, setPortAttr="mcast_rate", attrVal=0)
        env.switch[1].ui.modify_ports(device_ports, setPortAttr="bcast_rate", attrVal=0)

        # Define packets with different Dot1p tags.
        packet_1 = ({"Ethernet": {"dst": dst_3, "src": src_1, "type": 0x8100}},
                    {"Dot1Q": {"vlan": 1, "type": 0x0800, "prio": prio_higher}},
                    {"IP": {}})
        packet_2 = ({"Ethernet": {"dst": dst_3, "src": src_2, "type": 0x8100}},
                    {"Dot1Q": {"vlan": 1, "type": 0x0800, "prio": prio_lower}},
                    {"IP": {}})
        stream_1 = env.tg[1].set_stream(packet_1, iface=ports[('tg1', 'sw1')][1],
                                        rate=100, continuous=True)
        stream_2 = env.tg[1].set_stream(packet_2, iface=ports[('tg1', 'sw1')][2],
                                        rate=100, continuous=True)

        # Set Dot1p trust mode value on ingress port_1 and port_2.
        env.switch[1].ui.configure_port_cos(ports=[device_ports[0], device_ports[1]],
                                            trustMode="Dot1p")

        # Verify values have been changed
        for port in [device_ports[0], device_ports[1]]:
            port_qos_trust_mode = env.switch[1].ui.get_table_ports_qos_scheduling(port=port)
            assert port_qos_trust_mode['trustMode'] == "Dot1p", \
                'Trust mode value is not set to "Dot1p" for port %s' % port

        # Set Strict sched mode value on egress port_3.
        env.switch[1].ui.configure_port_cos(ports=[device_ports[2], ], schedMode="Strict")

        # Verify value has been changed
        port_qos_3_sched_mode = env.switch[1].ui.get_table_ports_qos_scheduling(port=device_ports[2])
        assert port_qos_3_sched_mode['schedMode'] == "Strict", \
            'Strict sched mode is not set on port %s' % ports[('sw1', 'tg1')][3]

        # Set Tagged value on egress port_3.
        env.switch[1].ui.modify_vlan_ports(ports=[device_ports[2], ],
                                           vlans=[1, ],
                                           tagged="Tagged")

        # Add Static MAC entry for egress port_3 definition.
        env.switch[1].ui.create_static_macs(device_ports[2], [1, ], [dst_3, ])

        # Set QoS statistic type for Dot1p definition on the TG port_3.
        env.tg[1].set_qos_stat_type(ports[('tg1', 'sw1')][3], "VLAN")

        # Need to wait until device generates all ICMP packets.
        time.sleep(5)

        # Send streams of packets with Dot1p priorities from the TG port_1 and port_2.
        env.tg[1].clear_statistics([ports[('tg1', 'sw1')][1],
                                    ports[('tg1', 'sw1')][2],
                                    ports[('tg1', 'sw1')][3], ])
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][3], ],
                              filter_layer="Dot1Q.IP",
                              src_filter=src_1,
                              dst_filter=dst_3)
        env.tg[1].start_streams([stream_1, stream_2, ])
        time.sleep(10)

        # Stop sending streams from TG port_1 and port_2.
        env.tg[1].stop_streams([stream_1, stream_2, ])
        time.sleep(0.5)
        env.tg[1].stop_sniff([ports[('tg1', 'sw1')][3], ], drop_packets=True)

        # Get count of sent packets on the TG port_1 and port_2.
        sent_count_stream_1 = env.tg[1].get_sent_frames_count(ports[('tg1', 'sw1')][1], )

        # Get count of received packets with Dot1p higher priority on TG port_3.
        dot1p_count_stream_1 = env.tg[1].get_qos_frames_count(ports[('tg1', 'sw1')][3],
                                                              prio_higher)
        if dot1p_count_stream_1 not in list(range(sent_count_stream_1,
                                             sent_count_stream_1 * 101 // 100)):
            pytest.fail("Packets with Dot1p higher priority are lost when default mapping is configured.")

        # Verify that filtered count of packets on TG port_3 is correct.
        filtered_count_stream_1 = env.tg[1].get_filtered_frames_count(ports[('tg1', 'sw1')][3], )
        if filtered_count_stream_1 != dot1p_count_stream_1:
            pytest.fail("Filter packets statistic has incorrect count of packets!")

        # Verify that not used queues don't receive any packets.
        if not self.not_used_cos_statistics(tg_instance=env.tg[1],
                                            prio_value_1=prio_higher,
                                            prio_value_2=prio_lower,
                                            iface=ports[('tg1', 'sw1')][3]):
            pytest.fail("Not used CoS statistics received unexpected packets!")

    @pytest.mark.skip("Pypacker does not support Vlan prio field")
    def test_qos_dscp_strict_mode(self, env):
        """
        @brief  Verify that packets with DSCP higher priority displace
                packets with DSCP lower priority by Strict schedule mode.
        @steps
            -# Set DSCP trust mode value on ingress port 1 and port 2.
            -# Set Strict sched mode value on egress port 3.
            -# Send two streams with different IP.tos values.
            -# Verify that packets with DSCP higher priority displace packets with DSCP lower priority
        @endsteps
        """
        prio_higher = 96
        prio_lower = 32

        src_1 = "00:00:00:00:01:11"
        src_2 = "00:00:00:00:02:22"
        dst_3 = "00:00:00:00:03:33"

         # Define active ports
        ports = env.get_ports([['sw1', 'tg1', 3], ])

        device_ports = list(ports[('sw1', 'tg1')].values())

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Disable Flow Control functionality
        env.switch[1].ui.modify_ports(device_ports, flowControl='None')
        for port in device_ports:
            env.switch[1].ui.wait_for_port_status(port, 'flowControl', 'None', 10)

        # Disable Cut Through functionality
        env.switch[1].ui.modify_ports(device_ports, cutThrough='Disabled')
        for port in device_ports:
            env.switch[1].ui.wait_for_port_status(port, 'cutThrough', 'Disabled', 10)

        # SetUp multicast and broadcast rate limits
        env.switch[1].ui.modify_ports(device_ports, setPortAttr="mcast_rate", attrVal=0)
        env.switch[1].ui.modify_ports(device_ports, setPortAttr="bcast_rate", attrVal=0)

        # Define packets with different TOS tags and configure streams of defined packets.
        packet_1 = ({"Ethernet": {"dst": dst_3, "src": src_1, "type": 0x0800}},
                    {"IP": {"tos": prio_higher}},
                    {"UDP": {}})
        packet_2 = ({"Ethernet": {"dst": dst_3, "src": src_2, "type": 0x0800}},
                    {"IP": {"tos": prio_lower}},
                    {"UDP": {}})
        stream_1 = env.tg[1].set_stream(packet_1, iface=ports[('tg1', 'sw1')][1],
                                        rate=100, continuous=True)
        stream_2 = env.tg[1].set_stream(packet_2, iface=ports[('tg1', 'sw1')][2],
                                        rate=100, continuous=True)

        # Set DSCP trust mode value on ingress port_1 and port_2.
        env.switch[1].ui.configure_port_cos(ports=device_ports[:2], trustMode="Dscp")
        for port in device_ports[:2]:
            port_qos_trust_mode = env.switch[1].ui.get_table_ports_qos_scheduling(port=port)
            assert port_qos_trust_mode['trustMode'] == "Dscp", \
                'Trust mode value is not set to "Dscp" for port %s' % port

        # Set Strict sched mode value on egress port_3.
        env.switch[1].ui.configure_port_cos(ports=[device_ports[2], ], schedMode="Strict")
        port_qos_3_sched_mode = env.switch[1].ui.get_table_ports_qos_scheduling(port=device_ports[2])
        assert port_qos_3_sched_mode['schedMode'] == "Strict", \
            'Strict sched mode is not set on port %s' % ports[('sw1', 'tg1')][3]

        # Add Static MAC entry for egress port_3 definition.
        env.switch[1].ui.create_static_macs(device_ports[2], [1, ], [dst_3, ])

        # Set QoS statistic type for DSCP definition on the TG port_3.
        env.tg[1].set_qos_stat_type(ports[('tg1', 'sw1')][3], "IP")

        # Need to wait until device generates all ICMP packets.
        time.sleep(5)

        # Send streams of packets with DSCP priorities from the TG port_1 and port_2.
        env.tg[1].clear_statistics([ports[('tg1', 'sw1')][1],
                                    ports[('tg1', 'sw1')][2],
                                    ports[('tg1', 'sw1')][3], ])
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][3], ],
                              src_filter=src_1,
                              dst_filter=dst_3)
        env.tg[1].start_streams([stream_1, stream_2, ])
        time.sleep(10)

        # Stop sending streams from TG port_1 and port_2.
        env.tg[1].stop_streams([stream_1, stream_2, ])
        time.sleep(0.5)
        env.tg[1].stop_sniff([ports[('tg1', 'sw1')][3], ], drop_packets=True)

        # Get count of sent packets on the TG port_1 and port_2.
        sent_count_stream_1 = env.tg[1].get_sent_frames_count(ports[('tg1', 'sw1')][1], )

        # Get count of received packets with DSCP higher priority on TG port_3.
        dscp_count_stream_1 = env.tg[1].get_qos_frames_count(ports[('tg1', 'sw1')][3],
                                                             (prio_higher // 32))
        if dscp_count_stream_1 not in list(range(sent_count_stream_1,
                                            sent_count_stream_1 * 101 // 100)):
            pytest.fail("Packets with DSCP higher priority are lost when default mapping configured.")

        # Verify that filtered count of packets on TG port_3 is correct.
        filtered_count_stream_1 = env.tg[1].get_filtered_frames_count(ports[('tg1', 'sw1')][3], )
        if filtered_count_stream_1 != dscp_count_stream_1:
            pytest.fail("Filter packets statistic has incorrect count of packets.")

        # Verify that not used queues don't receive any packets.
        if not self.not_used_cos_statistics(tg_instance=env.tg[1],
                                            prio_value_1=prio_higher // 32,
                                            prio_value_2=prio_lower // 32,
                                            iface=ports[('tg1', 'sw1')][3]):
            pytest.fail("Not used CoS statistics received unexpected packets.")

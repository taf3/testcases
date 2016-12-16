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

@file test_multicast_samples.py

@summary   Samples for Multicast configuration.

@details
Following test cases are tested:
1. Verify that multicast record can be added and deleted
2. Verify that multicast traffic is forwarded according to the L2Multicast table.
"""

import pytest

from testlib import helpers


@pytest.mark.multicast
@pytest.mark.simplified
class TestMulticastSamples(object):
    """
    @description Suite for Multicast testing
    """

    def test_multicast_entry(self, env):
        """
        @brief  Verify that multicast record can be added and deleted
        @steps
            -# Create Multicast record.
            -# Verify Multicast entry has been created.
            -# Delete Multicast record.
            -# Verify Multicast entry has been deleted.
        @endsteps
        """
        self.suite_logger.debug("Create and Verify Multicast record")
        # Add Multicast record
        mac = "01:00:5E:11:11:11"
        env.switch[1].ui.create_multicast(port=1, vlans=[1], macs=[mac])

        # Verify Multicast entry has been created
        multicast_table = env.switch[1].ui.get_table_l2_multicast()
        rec = {"portId": 1, "vlanId": 1, "macAddress": mac, "type": "Static"}
        assert rec in multicast_table, "Multicast {0} was not added".format(rec)

        self.suite_logger.debug("Delete Multicast record")
        # Remove Multicast
        env.switch[1].ui.delete_multicast(port=1, vlan=1, mac=mac)
        # Verify Multicast entry has been deleted
        multicast_table = env.switch[1].ui.get_table_l2_multicast()
        assert rec not in multicast_table, "Multicast {0} was not deleted".format(rec)

    def test_multicast_traffic(self, env):
        """
        @brief Verify that multicast traffic is forwarded according to the L2Multicast table.
        @steps
            -# Create Vlan 2.
            -# Add ports 1 and 2 into the created Vlan as Tagged.
            -# Create Multicast record with MAC '01:88:88:88:88:01' in Vlan 1 for port 2.
            -# Create Multicast record with MAC '01:88:88:88:88:02' in Vlan 2 for port 2.
            -# Send packet with Ethernet.dst '01:88:88:88:88:01' to the port 1
            -# Verify packet is forwarded to the port 2
            -# Send packet with Ethernet.dst '01:88:88:88:88:01' to the port 3
            -# Verify packet is forwarded to the port 2
            -# Send packet with Ethernet.dst '01:88:88:88:88:02' and Vlan 2 to the port 3
            -# Verify packet is forwarded to the port 2
            -# Send packet with Ethernet.dst '01:88:88:88:88:02' and Vlan 2 to the port 4
            -# Verify packet is forwarded to the port 2
        @endsteps
        """

        # Set active ports
        ports = env.get_ports([['tg1', 'sw1', 4], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Add Vlans:
        env.switch[1].ui.create_vlans(vlans=[2])

        # Add ports to vlans
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1],
                                                  ports[('sw1', 'tg1')][2]],
                                           vlans=[2],
                                           tagged='Tagged')

        # Add multicast records
        env.switch[1].ui.create_multicast(port=ports[('sw1', 'tg1')][2],
                                          vlans=[1],
                                          macs=['01:88:88:88:88:01'])
        env.switch[1].ui.create_multicast(port=ports[('sw1', 'tg1')][2],
                                          vlans=[2],
                                          macs=['01:88:88:88:88:02'])

        # Configure multicast streams
        packet_1 = ({'Ethernet': {'src': '00:11:11:11:11:11',
                               'dst': '01:88:88:88:88:01'}},
                    {'IP': {}})
        packet_2 = ({'Ethernet': {'src': '00:11:11:11:11:11',
                               'dst': '01:88:88:88:88:02',
                               'type': 0x8100}},
                    {'Dot1Q': {'vlan': 2}},
                    {'IP': {}})

        stream_1 = env.tg[1].set_stream(packet_1, count=1, iface=ports[('tg1', 'sw1')][1])
        stream_2 = env.tg[1].set_stream(packet_2, count=1, iface=ports[('tg1', 'sw1')][1])
        stream_3 = env.tg[1].set_stream(packet_1, count=1, iface=ports[('tg1', 'sw1')][3])
        stream_4 = env.tg[1].set_stream(packet_2, count=1, iface=ports[('tg1', 'sw1')][4])

        sniff_ports = list(ports[('tg1', 'sw1')].values())

        # Send stream 1
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)
        env.tg[1].send_stream(stream_1)
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print sniffed data
        helpers.print_sniffed_data_brief(data)

        # Verify that packet_1 is forwarded to the port 2
        params = ({"layer": 'Ethernet', "field": 'dst', "value": '01:88:88:88:88:01'},)
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][2], params,
                                                    data, env.tg[1])) == 1, \
            "Multicast packet is not forwarded on port 2"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][3], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 3"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][4], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 4"

        # Send stream 2
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)
        env.tg[1].send_stream(stream_2)
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print sniffed data
        helpers.print_sniffed_data_brief(data)

        # Verify that packet_2 is forwarded to the port 2
        params = ({"layer": 'Ethernet', "field": 'dst', "value": '01:88:88:88:88:02'},)
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][2], params,
                                                    data, env.tg[1])) == 1, \
            "Multicast packet is not forwarded on port 2"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][3], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 3"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][4], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 4"

        # Send stream 3
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)
        env.tg[1].send_stream(stream_3)
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print sniffed data
        helpers.print_sniffed_data_brief(data)

        # Verify that packet_3 is forwarded to the port 2
        params = ({"layer": 'Ethernet', "field": 'dst', "value": '01:88:88:88:88:01'},)
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][2], params,
                                                    data, env.tg[1])) == 1, \
            "Multicast packet is not forwarded on port 2"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][1], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 1"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][4], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 4"

        # Send stream 4
        env.tg[1].start_sniff(sniff_ports, sniffing_time=5)
        env.tg[1].send_stream(stream_4)
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print sniffed data
        helpers.print_sniffed_data_brief(data)

        # Verify that packet_4 is forwarded to the port 2
        params = ({"layer": 'Ethernet', "field": 'dst', "value": '01:88:88:88:88:02'},)
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][2], params,
                                                    data, env.tg[1])) == 1, \
            "Multicast packet is not forwarded on port 2"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][3], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 3"
        assert len(helpers.get_packet_from_the_port(ports[('tg1', 'sw1')][1], params,
                                                    data, env.tg[1])) == 0, \
            "Multicast packet is forwarded on port 1"

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

@file test_static_routes_samples.py

@summary   Samples for Static Routes configuration.

@details
Following test cases are tested:
1. Verify traffic forwarding upon two port on one VLAN and one Router Interface.
2. Verify static route behavior upon one port with two VLANs.
"""
import time

import pytest

from testlib import helpers


@pytest.mark.layer3
@pytest.mark.simplified
class TestStaticRoutesSamples(object):
    """
    @description Suite for Static Routes testing
    """

# Attributest and Properties

    def is_arp_added(self, arps=None, mac=None, ip=None):
        """
        @brief  Verify if ARP entry is available
        @param  arps:  list of ARP records
        @type  arps:  list[dict]
        @param  mac:  MAC Address
        @type  mac:  str
        @param  ip:  IP Address
        @type  ip:  str
        @rtype:  bool
        @return:  True if ARP is available
        """
        for arp in arps:
            if arp['phyAddress'].lower() == mac.lower() and arp['netAddress'] == ip:
                return True
        return False

# Test Cases

    def test_static_route_two_ports_in_one_vlan(self, env):
        """
        @brief  Verify traffic forwarding upon two port on one VLAN and one Router Interface.
        @steps
            -# Configure Vlan 10 on ports 1 and 2.
            -# Create Route Interface 20.0.10.1/24 on Vlan 10.
            -# Create Static Route 10.10.10.0/24 with nexthop 20.0.10.2.
            -# Verify ARP request 'who has 20.0.10.2' received on port 2.
            -# Send ARP reply.
            -# Send IP packet with IP.dst 10.10.10.101 to the port 1.
            -# Verify IP packet is routed to the port 2.
        @endsteps
        """
        # Define active ports.
        ports = env.get_ports([['tg1', 'sw1', 2], ])
        port_1 = ports[('sw1', 'tg1')][1]
        port_2 = ports[('sw1', 'tg1')][2]

        # Disabling all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch, wait_status=True)
        helpers.set_ports_admin_enabled(env.switch, ports, wait_status=True)

        # Define active ports for sniffing.
        sniff_ports = [ports[('tg1', 'sw1')][1], ports[('tg1', 'sw1')][2]]

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Enable Routing.
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)

        # Create test VLAN 10.
        env.switch[1].ui.create_vlans(vlans=[10])

        # Add port 1 and port 3 to created test VLAN.
        env.switch[1].ui.create_vlan_ports(ports=[port_1, port_2],
                                           vlans=[10], tagged='Tagged')

        # Add route interface.
        env.switch[1].ui.create_route_interface(10, '20.0.10.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Add Static route.
        env.switch[1].ui.create_static_route(ip='10.10.10.0/24',
                                             nexthop='20.0.10.2',
                                             network='20.0.10.1/24',
                                             distance=-1,
                                             mode='ip')

        # Get sniffer data
        data = env.tg[1].stop_sniff(sniff_ports)

        helpers.print_sniffed_data_brief(data)

        # Verify who-has "20.0.10.2" ARP requests received.
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": 'ff:ff:ff:ff:ff:ff'},
                    {"layer": "ARP", "field": 'tpa', "value": '20.0.10.2'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) >= 1, \
            "Packet is not received"

        # Get routers MAC.
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']

        # Send ARP reply to port 2.
        arp_reply = ({"Ethernet": {"src": "00:00:14:00:0a:02", "dst": route_mac.lower(), "type": 0x8100}},
                     {"Dot1Q": {"vlan": 10}},
                     {"ARP": {"op": 2, "sha": "00:00:14:00:0a:02",
                              "tha": route_mac, "tpa": "20.0.10.1", "spa": "20.0.10.2"}}, )
        stream_id = env.tg[1].set_stream(arp_reply, count=1, iface=ports[('tg1', 'sw1')][2])
        env.tg[1].send_stream(stream_id)

        time.sleep(2)

        # Verify ARP entry has been added
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert self.is_arp_added(arps=arp_table, mac='00:00:14:00:0a:02',
                                 ip='20.0.10.2'), 'ARP entry was not added'

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Send packet with source IP 20.0.10.101 and destination IP 10.10.10.101.
        packet_definition = ({"Ethernet": {"src": "00:00:10:00:02:65", "dst": route_mac, "type": 0x8100}},
                             {"Dot1Q": {"vlan": 10}},
                             {"IP": {"src": "20.0.10.101", "dst": "10.10.10.101", "p": 17}},
                             {"UDP": {"dport": 23, "sport": 23}})
        stream_id = env.tg[1].set_stream(packet_definition,
                                         count=1,
                                         iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id)

        # Stop sniffer
        data = env.tg[1].stop_sniff(sniff_ports)

        helpers.print_sniffed_data_brief(data)

        # Verify packet with destination 10.10.10.101 is not forwarded back to port 1.
        params_2 = [{"layer": "IP", "field": 'dst', "value": '10.10.10.101'},
                    {"layer": "IP", "field": 'src', "value": '20.0.10.101'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"

        # Verify packet is received from port 2.
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

    def test_static_route_one_ports_two_vlans(self, env):
        """
        @brief  Verify static route behaviour upon one port with two VLANs.
        @steps
            -# Configure Vlans 12 and 34 on port 1.
            -# Set pvid 12 for port 1.
            -# Create Route Interface 20.0.12.1/24 on Vlan 12.
            -# Create Route Interface 20.0.34.1/24 on Vlan 34.
            -# Create Static Route 10.10.10.0/24 with nexthop 20.0.34.5.
            -# Verify ARP request 'who has 20.0.34.5' received.
            -# Send ARP reply.
            -# Send IP packet with IP.dst 10.10.10.101 to the port 1.
            -# Verify IP packet is routed to the port 1.
        @endsteps
        """
        ports = env.get_ports([['tg1', 'sw1', 1], ])
        port_1 = ports[('sw1', 'tg1')][1]

        # Disabling all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch, wait_status=True)
        helpers.set_ports_admin_enabled(env.switch, ports, wait_status=True)

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Define active ports for sniffing.
        sniff_ports = [ports[('tg1', 'sw1')][1], ]

        # Enable Routing.
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)

        # Create test VLAN 10.
        env.switch[1].ui.create_vlans(vlans=[12, 34])

        # Delete port 1 from default VLAN.
        env.switch[1].ui.delete_vlan_ports(ports=[port_1], vlans=[1])

        # Add port 1 to created test VLANs.
        env.switch[1].ui.create_vlan_ports(ports=[port_1],
                                           vlans=[12, 34], tagged='Tagged')

        # Set proper pvid for port 1
        env.switch[1].ui.modify_ports(ports=[port_1], pvid=12)

        # Add route interfaces.
        env.switch[1].ui.create_route_interface(12, '20.0.12.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')
        env.switch[1].ui.create_route_interface(34, '20.0.34.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Add Static route.
        env.switch[1].ui.create_static_route(ip='10.10.10.0/24',
                                             nexthop='20.0.34.5',
                                             network='20.0.34.1/24',
                                             distance=-1,
                                             mode='ip')

        # Get sniffer data
        data = env.tg[1].stop_sniff(sniff_ports)

        helpers.print_sniffed_data_brief(data)

        # Verify who-has "20.0.34.5" ARP requests received.
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": 'ff:ff:ff:ff:ff:ff'},
                    {"layer": "ARP", "field": 'pdst', "value": '20.0.34.5'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) >= 1, \
            "Packet is not received"

        # Get routers MAC.
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']

        # Send ARP reply to port 2.
        arp_reply = ({"Ethernet": {"src": "00:00:14:00:22:05", "dst": route_mac.lower(), "type": 0x8100}},
                     {"Dot1Q": {"vlan": 34}},
                     {"ARP": {"op": 2, "sha": "00:00:14:00:22:05",
                              "tha": route_mac, "tpa": "20.0.34.1", "spa": "20.0.34.5"}}, )
        stream_id = env.tg[1].set_stream(arp_reply, count=1, iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id)

        time.sleep(2)

        # Verify ARP entry has been added
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert self.is_arp_added(arps=arp_table, mac='00:00:14:00:22:05',
                                 ip='20.0.34.5'), 'ARP entry was not added'

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Send to switch port 1 untagged IP packet with destination IP 10.10.10.101.
        packet_definition = ({"Ethernet": {"src": "00:00:20:00:10:65", "dst": route_mac, "type": 0x0800}},
                             {"IP": {"src": "20.0.12.101", "dst": "10.10.10.101", "p": 17}},
                             {"UDP": {"dport": 23, "sport": 23}})
        stream_id = env.tg[1].set_stream(packet_definition,
                                         count=1,
                                         iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id)

        # Stop sniffer
        data = env.tg[1].stop_sniff(sniff_ports)

        helpers.print_sniffed_data_brief(data)

        # Verify that TG port 1 receive IP packet with destination 10.10.10.101
        params_2 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:14:00:22:05'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()},
                    {"layer": "IP", "field": 'src', "value": '20.0.12.101'},
                    {"layer": "IP", "field": 'dst', "value": '10.10.10.101'},
                    {"layer": "Dot1Q", "field": 'vlan', "value": 34}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
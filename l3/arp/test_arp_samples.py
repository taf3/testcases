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
@file test_fdb_samples.py

@summary   Samples for FDB configuration.

@details
Following test cases are tested:
1. Verify that ARP configuration can be modified.
2. Verify that Static ARP entry can be created and deleted.
3. Verify that traffic is processed according to the created Static ARP.
4. Verify that Dynamic ARP entry can be learned.
5. Verify that traffic is processed according to the learned Dynamic ARP.
"""

import pytest

from testlib import helpers


@pytest.mark.layer3
@pytest.mark.simplified
class TestArpSamples(object):
    """
    @description Suite for ARP testing
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

    def test_arp_configuration(self, env):
        """
        @brief  Verify that ARP configuration can be modified
        @steps
            -# Verify the default ARP configuration.
            -# Change ARP configuration.
            -# erify changes have been applied.
        @endsteps
        """
        # Get ARP configuration
        config = env.switch[1].ui.get_table_arp_config()
        # Verify default values
        assert config[0]['AcceptGARP'] == 'True'
        assert config[0]['RefreshPeriod'] == 30
        assert config[0]['RequestDelay'] == 1
        assert config[0]['SecureMode'] == 'False'
        assert config[0]['AgeTime'] == 300
        assert config[0]['NumAttempts'] == 3

        # Change ARP configuration
        env.switch[1].ui.configure_arp(age_time=600, attemptes=5)

        # Verify changes have been applied
        config = env.switch[1].ui.get_table_arp_config()

        assert config[0]['AgeTime'] == 600
        assert config[0]['NumAttempts'] == 5

    def test_static_arp(self, env):
        """
        @brief  Verify that Static ARP entry can be created and deleted.
        @steps
            -# Perform device preconfiguration.
            -# Create static ARP record.
            -# Verify static ARP has been created.
            -# Delete static ARP record.
            -# Verify static ARP has been deleted.
        @endsteps
        """
        # Perform device preconfiguration: add vlan and route interface
        env.switch[1].ui.create_vlans(vlans=[10])
        env.switch[1].ui.create_vlan_ports(ports=[1, 2], vlans=[10], tagged='Tagged')
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)
        env.switch[1].ui.create_route_interface(10, '10.10.10.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        self.suite_logger.debug("Create and Verify Static ARP record")

        # Add static ARP record
        env.switch[1].ui.create_arp('10.10.10.10', '00:00:0a:0a:0a:0a', '10.10.10.1/24',
                                    mode='arp')

        # Verify static ARP has been created
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert self.is_arp_added(arps=arp_table,
                                 mac='00:00:0a:0a:0a:0a',
                                 ip='10.10.10.10'), 'ARP entry was not added'

        self.suite_logger.debug("Delete Static ARP record")
        # Remove static ARP
        env.switch[1].ui.delete_arp('10.10.10.10', '10.10.10.1/24', mode='arp')
        # Verify static ARP has been deleted
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert not self.is_arp_added(arps=arp_table, mac='00:00:0a:0a:0a:0a',
                                     ip='10.10.10.10'), 'ARP entry was not removed'

    def test_static_arp_traffic(self, env):
        """
        @brief  Verify that traffic is processed according to the created Static ARP.
        @steps
            -# Perform device preconfiguration.
            -# Create static ARP record.
            -# Send IP packets, related to the ARP record, to the first port.
            -# Verify IP packet is routed.
        @endsteps
        """
        # Get active ports: use two ports for test case
        ports = env.get_ports([['tg1', 'sw1', 2], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        self.suite_logger.debug("Perform test preconfiguration")
        env.switch[1].ui.create_vlans(vlans=[10, 20])
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1], ],
                                           vlans=[10], tagged='Untagged')
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][2], ],
                                           vlans=[20], tagged='Untagged')
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][1], ], pvid=10)
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][2], ], pvid=20)
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)
        env.switch[1].ui.create_route_interface(10, '10.10.10.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')
        env.switch[1].ui.create_route_interface(20, '20.20.20.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        self.suite_logger.debug("Create Static ARP")
        # Create static ARP record for second port
        env.switch[1].ui.create_arp('20.20.20.20', '00:00:14:14:14:14', '20.20.20.1/24',
                                    mode='arp')

        # Generate test traffic
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']
        packet_1 = ({"Ethernet": {"dst": route_mac, "src": "00:00:0a:0a:0a:0a", "type": 0x8100}},
                    {"Dot1Q": {"vlan": 10}},
                    {"IP": {"dst": '20.20.20.20', "src": '10.10.10.10'}},
                    {"TCP": {}})
        # Send packets to the first port
        stream = env.tg[1].set_stream(packet_1, count=1, iface=ports[('tg1', 'sw1')][1])

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][2]], sniffing_time=10)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff([ports[('tg1', 'sw1')][2]])

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify traffic is processed according to the ARP records")
        # Get packets from the captured data
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:14:14:14:14'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()},
                    {"layer": "IP", "field": 'dst', "value": '20.20.20.20'},
                    {"layer": "IP", "field": 'src', "value": '10.10.10.10'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=ports[('tg1', 'sw1')][2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

    def test_dynamic_arp(self, env):
        """
        @brief  Verify that Dynamic ARP entry can be learned.
        @steps
            -# Perform device preconfiguration.
            -# Send IP traffic.
            -# Verify ARP request has been sent.
            -# Send ARP reply.
            -# Verify dynamic ARP record has been added.
        @endsteps
        """
        # Perform device preconfiguration: add vlan and route interface
        # Get active ports: use two ports for test case
        ports = env.get_ports([['tg1', 'sw1', 2], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        self.suite_logger.debug("Perform test preconfiguration")
        env.switch[1].ui.create_vlans(vlans=[10, 20])
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1], ],
                                           vlans=[10], tagged='Untagged')
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][2], ],
                                           vlans=[20], tagged='Untagged')
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][1], ], pvid=10)
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][2], ], pvid=20)
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)
        env.switch[1].ui.create_route_interface(10, '10.10.10.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')
        env.switch[1].ui.create_route_interface(20, '20.20.20.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        # Generate test traffic
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']
        packet_1 = ({"Ethernet": {"dst": route_mac, "src": "00:00:0a:0a:0a:0a", "type": 0x8100}},
                    {"Dot1Q": {"vlan": 10}},
                    {"IP": {"dst": '20.20.20.20', "src": '10.10.10.10'}},
                    {"TCP": {}})
        # Send packets to the first port
        stream = env.tg[1].set_stream(packet_1, count=1, iface=ports[('tg1', 'sw1')][1])

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][2]], sniffing_time=10)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff([ports[('tg1', 'sw1')][2]])

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify ARP request has been sent")
        # Get packets from the captured data
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": 'ff:ff:ff:ff:ff:ff'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()},
                    {"layer": "ARP", "field": 'op', "value": 1},
                    {"layer": "ARP", "field": 'tpa', "value": '20.20.20.20'},
                    {"layer": "ARP", "field": 'spa', "value": '20.20.20.1'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=ports[('tg1', 'sw1')][2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) >= 1, \
            "Packet is not received"

        # Send ARP reply
        arp_reply = ({"Ethernet": {"dst": route_mac, "src": "00:00:14:14:14:14", "type": 0x8100}},
                     {"Dot1Q": {"vlan": 20}},
                     {"ARP": {"op": 2, "sha": "00:00:14:14:14:14", "tha": route_mac,
                              "spa": "20.20.20.20", "tpa": "20.20.20.1"}})

        arp_stream = env.tg[1].set_stream(arp_reply,
                                          count=1,
                                          iface=ports[('tg1', 'sw1')][2])

        env.tg[1].send_stream(arp_stream)

        # Verify ARP entry has been added
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert self.is_arp_added(arps=arp_table, mac='00:00:14:14:14:14',
                                 ip='20.20.20.20'), 'ARP entry was not added'

    def test_dynamic_arp_traffic(self, env):
        """
        @brief  Verify that traffic is processed according to the learned Dynamic ARP.
        @steps
            -# Perform device preconfiguration.
            -# Send IP traffic.
            -# Verify ARP request has been sent.
            -# Send ARP reply.
            -# Send IP packets, related to the ARP record, to the first port.
            -# Verify IP packet is routed.
        @endsteps
        """

        # Perform device preconfiguration: add vlan and route interface
        # Get active ports: use two ports for test case
        ports = env.get_ports([['tg1', 'sw1', 2], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        self.suite_logger.debug("Perform test preconfiguration")
        env.switch[1].ui.create_vlans(vlans=[10, 20])
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1], ],
                                           vlans=[10], tagged='Untagged')
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][2], ],
                                           vlans=[20], tagged='Untagged')
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][1], ], pvid=10)
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][2], ], pvid=20)
        env.switch[1].ui.configure_routing(routing='Enabled', ospf=None)
        env.switch[1].ui.create_route_interface(10, '10.10.10.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')
        env.switch[1].ui.create_route_interface(20, '20.20.20.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        # Generate test traffic
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']
        packet_1 = ({"Ethernet": {"dst": route_mac, "src": "00:00:0a:0a:0a:0a", "type": 0x8100}},
                    {"Dot1Q": {"vlan": 10}},
                    {"IP": {"dst": '20.20.20.20', "src": '10.10.10.10'}},
                    {"TCP": {}})
        # Send packets to the first port
        stream = env.tg[1].set_stream(packet_1, count=1, iface=ports[('tg1', 'sw1')][1])

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][2]], sniffing_time=10)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff([ports[('tg1', 'sw1')][2]])

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify ARP request has been sent")
        # Get packets from the captured data
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": 'ff:ff:ff:ff:ff:ff'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()},
                    {"layer": "ARP", "field": 'op', "value": 1},
                    {"layer": "ARP", "field": 'tpa', "value": '20.20.20.20'},
                    {"layer": "ARP", "field": 'spa', "value": '20.20.20.1'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=ports[('tg1', 'sw1')][2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) >= 1, \
            "Packet is not received"

        # Send ARP reply
        arp_reply = ({"Ethernet": {"dst": route_mac, "src": "00:00:14:14:14:14", "type": 0x8100}},
                     {"Dot1Q": {"vlan": 20}},
                     {"ARP": {"op": 2, "sha": "00:00:14:14:14:14", "tha": route_mac,
                              "spa": "20.20.20.20", "tpa": "20.20.20.1"}})

        arp_stream = env.tg[1].set_stream(arp_reply, count=1, iface=ports[('tg1', 'sw1')][2])

        env.tg[1].send_stream(arp_stream)

        # Verify ARP entry has been added
        arp_table = env.switch[1].ui.get_table_arp(mode='arp')
        assert self.is_arp_added(arps=arp_table,
                                 mac='00:00:14:14:14:14',
                                 ip='20.20.20.20'), 'ARP entry was not added'

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff([ports[('tg1', 'sw1')][2]], sniffing_time=10)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff([ports[('tg1', 'sw1')][2]])

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify traffic is processed according to the ARP records")
        # Get packets from the captured data
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:14:14:14:14'},
                    {"layer": "Ethernet", "field": 'src', "value": route_mac.lower()},
                    {"layer": "IP", "field": 'dst', "value": '20.20.20.20'},
                    {"layer": "IP", "field": 'src', "value": '10.10.10.10'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=ports[('tg1', 'sw1')][2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

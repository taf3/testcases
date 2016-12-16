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

@file test_ospf_samples.py

@summary   Samples for OSPFv2 configuration.

@details
Following test cases are tested:
1. Verify OSPF hello packet has correct fields after OSPF protocol initialization.
2. Verify that Routes table accommodates at least 1k entries using OSPF routes.
"""
import time

import pytest

from testlib import helpers


@pytest.mark.layer3
class TestOSPFSamples(object):
    """
    @description Suite for OSPFv2 testing
    """

# Attributest and Properties

    def _wait_for_route_table_loading(self, switch, interval, record_count):
        """
        @brief  Wait for Route table has certain number of records
        @param  switch:  switch for checking Route table
        @type  switch:  SwitchGeneral
        @param  interval:  seconds for checking Routes table
        @type  interval:  int
        @param  record_count:  expected number of records in Route table
        @typr  record_count:  int
        @raise: pytest.fail in case Route table doesn't contain expected number of records
        @return  None
        @par  Example:
        @code
        self._wait_for_route_table_loading(env.switch[1], 120, 9)
        @endcode
        """
        end_time = time.time() + interval
        start_count = 0
        while time.time() <= end_time:
            table_length = len(switch.ui.get_table_route())
            # Add log message on lenght changes
            if table_length != start_count:
                self.suite_logger.debug('Route table has {} records'.format(table_length))
                start_count = table_length
            if table_length >= record_count:
                return
            # Route table needs long time to update
            time.sleep(20)
        pytest.fail("Route table does not have {} records after {} seconds elapsed".format(record_count, interval))

    @pytest.mark.simplified
    @pytest.mark.skip("Pypacker does not support OSPF protocol properly")
    def test_ospf_hello_packets(self, env):
        """
        @brief Verify OSPF hello packet has correct fields after OSPF protocol initialization.
        @steps
            -# Add Vlan 100, set pvid on ports 1 to 100
            -# Configure OSPF on DUT (area 0.0.0.0)
            -# Create Route Interface (10.0.1.0 on vlan 100)
            -# Add Route Interface to the OSPF Area
            -# Start capture for OSPF Hello packets
            -# Verify OSPF Hello packets were received
        @endsteps
        """
        # Define ports.
        ports = env.get_ports([['tg1', 'sw1', 1], ])
        sniff_ports = [ports[('tg1', 'sw1')][1], ]

        # Disabling all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports, wait_status=True)

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Enable Routing.
        env.switch[1].ui.configure_routing(routing='Enabled', ospf='Enabled')

        # Configuring general OSPF parameters for four switches.
        env.switch[1].ui.configure_ospf_router(logAdjacencyChanges='Enabled',
                                               routerId='1.1.1.1')

        # Create test VLAN 100.
        env.switch[1].ui.create_vlans(vlans=[100])

        # Deleting ports from default VLAN.
        env.switch[1].ui.delete_vlan_ports(ports=[ports[('sw1', 'tg1')][1]], vlans=[1])

        # Adding ports to created test VLANs.
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1], ],
                                           vlans=[100], tagged='Tagged')

        # Set pvid for VLANs ports.
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][1], ], pvid=100)

        # Configuring general OSPF Area parameters.
        env.switch[1].ui.create_ospf_area('0.0.0.0')

        # Adding OSPF route intefaces.
        env.switch[1].ui.create_route_interface(100, '10.0.1.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        env.switch[1].ui.create_network_2_area(network='10.0.1.1/24',
                                               area='0.0.0.0',
                                               mode='Disabled')

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=35)

        # Stop sniffer.
        data = env.tg[1].stop_sniff(sniff_ports)

        # Verify Ethernet and IP header of OSPF Hello packet.
        route_mac = env.switch[1].ui.get_table_route_interface()[0]['mac']

        # Verify source MAC address belongs to route interface.
        assert sniff_ports[0] in data, 'OSPF Hello packets are not received!'
        check_pac_fields = False
        i = 0
        packet_time = []
        for packet in data[sniff_ports[0]]:
            # Verify source MAC address belongs to route interface.
            if env.tg[1].check_packet_field(packet, layer="Ethernet",
                                            field="src", value=route_mac.lower()):
                # Verify destination MAC is 01:00:5E:00:00:05.
                if env.tg[1].check_packet_field(packet, layer="Ethernet",
                                                field="dst", value="01:00:5E:00:00:05"):
                    # Verify correct VLAN Tag.
                    assert env.tg[1].check_packet_field(packet, layer="Dot1Q",
                                                        field="vlan", value=100)
                    # Verify source IP belongs to Route Interface.
                    assert env.tg[1].check_packet_field(packet, layer="IP",
                                                        field="src", value="10.0.1.1")
                    # Verify destination IP is 224.0.0.5.
                    assert env.tg[1].check_packet_field(packet, layer="IP",
                                                        field="dst", value="224.0.0.5")
                    # Verify OSPF header: OSPF version = 2.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hdr",
                                                        field="version", value=2)
                    # Verify OSPF header: Message type = 1.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hdr",
                                                        field="type", value=1)
                    # Verify OSPF header: Correct Router ID of the originating router.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hdr",
                                                        field="src", value="1.1.1.1")
                    # Verify OSPF header: The Area ID of the originating router interface.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hdr",
                                                        field="area", value="0.0.0.0")
                    # Verify Hello part: The address mask of the originating interface.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="mask", value="255.255.255.0")
                    # Verify Hello part: The HelloInterval of the originating interface.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="hellointerval", value=10)
                    # Verify Hello part: The RouterDeadInterval of the originating interface.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="deadinterval", value=40)
                    # Verify Hello part: The Router Priority.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="prio", value=1)
                    # Verify Hello part: The DR and BDR
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="backup", value="0.0.0.0")
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="router", value="0.0.0.0")
                    # Verify Hello part: Five flag bits signifying optional capabilities.
                    assert env.tg[1].check_packet_field(packet, layer="OSPF_Hello",
                                                        field="options", value=0x02)
                    packet_time.insert(i, packet.time)
                    i += 1
                    check_pac_fields = True
        assert check_pac_fields, "Received OSPF Hello packet is inccorect."

        # Verify time delay between hello packets is 10 seconds by default.
        hello_interval = packet_time[2] - packet_time[1]
        self.suite_logger.debug("Delay between hello packets is {} (should be 10 secconds)".format(hello_interval))
        assert int(hello_interval) in range(9, 11), "Delay between hello packets is incorrect"

    @pytest.mark.ixnet_simplified
    @pytest.mark.skipif("not config.env.tg[1].is_protocol_emulation_present", reason="IxNetwork only test case.")
    def test_routes_table_max_records_count_same_area_traffic_2_ports(self, env):
        """
        @brief  Verify that Routes table accommodates at least 1k entries using OSPF routes
        @steps
            -# Add Vlans 100 and 200, set pvid on ports 1 and 2 to 100 and 200
            -# Configure OSPF on DUT (area 0.0.0.0)
            -# Create Route Interfaces (10.1.0.0 on vlan 100, 10.2.0.0 on vlan 200)
            -# Configure OSPF router 2.2.2.2 with 512 routes in route range in IxNetwork on port 1
            -# Configure OSPF router 3.3.3.3 with 512 routes in route range in IxNetwork on port 2
            -# Start OSPF on IxNetwork
            -# Wait for DUT's'Route table has 1k records
            -# Create bidirectional traffic item with src in routes on port 1 and dst in routes from port 2
            -# Start traffic on IxNetwork
            -# Verify traffic loss is not observed
        @endsteps
        """
        ports = env.get_ports([['tg1', 'sw1', 2], ])

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # ===================================   Configure device   =====================================================
        # Add entry to Vlans Table
        env.switch[1].ui.create_vlans(vlans=[100, 200])

        env.switch[1].ui.delete_vlan_ports(ports=[ports[('sw1', 'tg1')][1],
                                                  ports[('sw1', 'tg1')][2]],
                                           vlans=[1])

        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][1], ],
                                           vlans=[100], tagged='Untagged')
        env.switch[1].ui.create_vlan_ports(ports=[ports[('sw1', 'tg1')][2], ],
                                           vlans=[200], tagged='Untagged')

        # Setting Primary VLAN ID for ports
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][1], ], pvid=100)
        env.switch[1].ui.modify_ports(ports=[ports[('sw1', 'tg1')][2], ], pvid=200)

        # Configuring general OSPF params
        env.switch[1].ui.configure_routing(routing='Enabled', ospf='Enabled')
        env.switch[1].ui.configure_ospf_router(logAdjacencyChanges='Enabled',
                                               routerId='1.1.1.1')

        # Adding default OSPF area
        env.switch[1].ui.create_ospf_area('0.0.0.0')

        # Adding OSPF route intefaces
        env.switch[1].ui.create_route_interface(100, '10.1.0.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')
        env.switch[1].ui.create_route_interface(200, '10.2.0.1/24', ip_type='InterVlan',
                                                bandwidth=1000, mtu=1500,
                                                status='Enabled', vrf=0, mode='ip')

        # "OSPF Networks 2 Area"
        env.switch[1].ui.create_network_2_area(network='10.1.0.1/24',
                                               area='0.0.0.0',
                                               mode='Disabled')
        env.switch[1].ui.create_network_2_area(network='10.2.0.1/24',
                                               area='0.0.0.0',
                                               mode='Disabled')

        # ===================================   Configure IxNetwork   =====================================================
        tgport1 = ports[('tg1', 'sw1')][1]
        tgport2 = ports[('tg1', 'sw1')][2]

        increment_count = 512

        session_handle_1 = env.tg[1].OSPF.config(tgport1,
                                                 reset=True,
                                                 mode="create",
                                                 mac_address_init="0000.0a01.0002",
                                                 intf_ip_addr="10.1.0.2",
                                                 router_id="2.2.2.2",
                                                 area_id="0.0.0.0",
                                                 router_priority=1,
                                                 neighbor_intf_ip_addr="10.1.0.1",
                                                 lsa_discard_mode=0,
                                                 enable_dr_bdr=1,
                                                 mtu=1500,
                                                 session_type="ospfv2")

        env.tg[1].OSPF.topology_route_config(session_handle_1,
                                             summary_number_of_prefix=increment_count,
                                             summary_prefix_start='192.168.1.1',
                                             summary_prefix_length=24,
                                             summary_prefix_metric=20,
                                             summary_route_type="another_area",
                                             type="summary_routes")

        session_handle_2 = env.tg[1].OSPF.config(tgport2,
                                                 reset=True,
                                                 mode="create",
                                                 mac_address_init="0000.0a02.0002",
                                                 intf_ip_addr="10.2.0.2",
                                                 router_id="3.3.3.3",
                                                 area_id="0.0.0.0",
                                                 router_priority=1,
                                                 neighbor_intf_ip_addr="10.2.0.1",
                                                 lsa_discard_mode=0,
                                                 enable_dr_bdr=1,
                                                 mtu=1500,
                                                 session_type="ospfv2")

        env.tg[1].OSPF.topology_route_config(session_handle_2,
                                             summary_number_of_prefix=increment_count,
                                             summary_prefix_start='193.168.1.1',
                                             summary_prefix_length=24,
                                             summary_prefix_metric=20,
                                             summary_route_type="another_area",
                                             type="summary_routes")

        env.tg[1].OSPF.ospf_control(session_handle_1)
        env.tg[1].OSPF.ospf_control(session_handle_2)

        # Wait some time for Route table loading
        self._wait_for_route_table_loading(env.switch[1], 600, 1024)

        # ===================================   Generate traffic   =====================================================

        env.tg[1].traffic_config(mode='create',
                                 transmit_mode='continuous',
                                 src_dest_mesh='fully',
                                 route_mesh='one_to_one',
                                 circuit_type='none',
                                 circuit_endpoint_type='ipv4',
                                 emulation_src_handle="$%s" % (session_handle_1, ),
                                 emulation_dst_handle="$%s" % (session_handle_2, ),
                                 rate_percent=99,
                                 length_mode='fixed',
                                 frame_size=64)

        env.tg[1].traffic_control(action='run')

        time.sleep(60)

        env.tg[1].traffic_control(action='stop')

        time.sleep(15)

        env.tg[1].traffic_stats(tgport1)
        env.tg[1].traffic_stats(tgport2)

        # Get statistics
        send_1 = int(env.tg[1].traffic_dictionary[tgport1]['stats']['aggregate']['tx']['total_pkts'])
        send_2 = int(env.tg[1].traffic_dictionary[tgport2]['stats']['aggregate']['tx']['total_pkts'])
        receive_1 = int(env.tg[1].traffic_dictionary[tgport1]['stats']['aggregate']['rx']['total_pkts'])
        receive_2 = int(env.tg[1].traffic_dictionary[tgport2]['stats']['aggregate']['rx']['total_pkts'])

        assert 0 < receive_2 - send_1 < 40, "Packet loss is observed"
        assert 0 < receive_1 - send_2 < 40, "Packet loss is observed"

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

@file test_qinq_samples.py

@summary   Samples for QinQ configuration.

@details
Following test cases are tested:
1. Verify that packet sent without double-tag from one Vlan to another is received on the correct port with double-tag (Vlan Stacking).
2. Verify that customer unmapped packet is received on correct port if provider mapped packet from one Vlan to another is send (Using Vlan Mapping).

"""
import time

import pytest

from testlib import helpers


@pytest.mark.qinq
@pytest.mark.simplified
class TestQinQSamples(object):
    """
    @description Suite for QinQ testing
    """

    @pytest.mark.skip("Pypacker does not support QinQ")
    def test_qinq_vlan_stacking(self, env):
        """
        @brief  Verify that packet sent without double-tag from one Vlan to another
                is received on the correct port with double-tag (Vlan Stacking)
        @steps
            -# Configure Vlan 10 on port 1.
            -# Configure Vlan 100 on ports 1 and 2.
            -# Configure port 1 as CustomerStacked.
            -# Configure port 2 as ProviderStacked.
            -# Configure Vlan Stacking for port 1, provider vlan 100.
            -# Send packet with vlan 10 to the port 1.
            -# Verify that packet is double tagged on port 2
        @endsteps
        """
        destination_mac = "01:00:5E:00:01:05"
        source_mac = "00:00:00:00:08:22"
        vlan_id_customer = 10
        vlan_id_provider = 100
        vlan_priority_customer = 5
        vlan_priority_provider = 6

        ports = env.get_ports([['tg1', 'sw1', 2], ])

        sniff_ports = list(ports[('tg1', 'sw1')].values())

        # Disable all ports and enabling only necessary ones
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        port_id_customer = ports[('sw1', 'tg1')][1]
        port_id_provider = ports[('sw1', 'tg1')][2]

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Generate customer and provider vlans
        env.switch[1].ui.create_vlans(vlans=[vlan_id_customer, vlan_id_provider])

        # Add port to customer vlan
        env.switch[1].ui.create_vlan_ports(ports=[port_id_customer],
                                           vlans=[vlan_id_customer],
                                           tagged='Tagged')

        # Add port to provider vlan
        env.switch[1].ui.create_vlan_ports(ports=[port_id_provider],
                                           vlans=[vlan_id_provider],
                                           tagged='Tagged')

        # Add customer port to provider vlan
        env.switch[1].ui.create_vlan_ports(ports=[port_id_customer],
                                           vlans=[vlan_id_provider],
                                           tagged='Untagged')

        # Add entries about customer and provider to ports table
        env.switch[1].ui.configure_qinq_ports([port_id_customer], mode='CustomerStacked')
        env.switch[1].ui.configure_qinq_ports([port_id_customer], tpid=33024)

        env.switch[1].ui.configure_qinq_ports([port_id_provider], mode='ProviderStacked')
        env.switch[1].ui.configure_qinq_ports([port_id_provider], tpid=37120)

        # Set options for vlan stacking
        env.switch[1].ui.configure_qinq_vlan_stacking([port_id_customer],
                                                      vlan_id_provider,
                                                      vlan_priority_provider)

        # Define packet without double tag
        packet_definition = ({"Ethernet": {"dst": destination_mac,
                                        "src": source_mac,
                                        "type": 0x8100}},
                             {"Dot1Q": {"vlan": vlan_id_customer,
                                        "type": 0x0800,
                                        "prio": vlan_priority_customer}},
                             {"IP": {}})

        #Wait some time to add all rows to tables
        time.sleep(1)

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Send one packet to the test port
        stream_id = env.tg[1].set_stream(packet_definition,
                                         count=1,
                                         iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id)

        data = env.tg[1].stop_sniff(sniff_ports)

        helpers.print_sniffed_data_brief(data)

        # Verify that packet is sending without double-tag from one Vlan
        # to another it will be received in correct port with double-tag
        assert sniff_ports[1] in list(data.keys()), "No packet on expected port"

        params = [{"layer": "Ethernet", "field": 'src', "value": source_mac.lower()}]
        packet = helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                  params=params,
                                                  sniff_data=data,
                                                  tg=env.tg[1])[0]
        assert env.tg[1].check_packet_field(packet=packet,
                                            layer="Ethernet",
                                            field="type",
                                            value=37120), \
            "Field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet,
                                            layer="Dot1Q",
                                            field="vlan",
                                            value=vlan_id_provider), \
            "Vlan field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet,
                                            layer="Dot1Q",
                                            field="prio",
                                            value=vlan_priority_provider), \
            "Prio field value isn't equal to expected"

        layers = env.tg[1].packet_dictionary(packet)
        dot1q_counter = len([x for x in layers if "Dot1Q" in x])
        assert dot1q_counter == 2

    @pytest.mark.skip("Pypacker does not support QinQ")
    def test_qinq_vlan_mapping(self, env):
        """
        @brief  Verify that customer unmapped packet is received on correct port
                if provider mapped packet from one Vlan to another is send (Using Vlan Mapping)
        @steps
            -# Configure Vlans 200 and 300 on ports 1 and 2.
            -# Configure port 1 as CustomerMapped.
            -# Configure port 2 as ProviderMapped.
            -# Configure Vlan Mapping for port 1, customer vlan 20, provider vlan 200.
            -# Configure Vlan Mapping for port 1, customer vlan 30, provider vlan 300.
            -# Send packet with vlan 200 to the port 1.
            -# Send packet with vlan 300 to the port 1.
            -# Verify that packets are received on port 2 with correct customer Vlan IDs.
        @endsteps
        """
        destination_mac = "00:80:C2:04:00:00"
        source_mac = "00:00:00:00:02:22"
        destination_mac1 = "00:80:C2:02:00:00"
        source_mac1 = "00:00:00:00:00:42"
        vlan_id_customer1 = 20
        vlan_id_customer2 = 30
        vlan_id_provider1 = 200
        vlan_id_provider2 = 300
        tp_id_2 = 33024
        vlan_priority_customer = 2
        vlan_priority_provider = 4

        ports = env.get_ports([['tg1', 'sw1', 2], ])

        sniff_ports = list(ports[('tg1', 'sw1')].values())

        # Disable all ports and enable only necessary ones
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        port_id_customer = ports[('sw1', 'tg1')][1]
        port_id_provider = ports[('sw1', 'tg1')][2]

        # Disable STP
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Generate two vlans
        env.switch[1].ui.create_vlans(vlans=[vlan_id_provider1, vlan_id_provider2])

        # Add second port to provider vlans
        env.switch[1].ui.create_vlan_ports(ports=[port_id_provider],
                                           vlans=[vlan_id_provider1,
                                                  vlan_id_provider2],
                                           tagged='Tagged')

        # Add customer port to provider vlans
        env.switch[1].ui.create_vlan_ports(ports=[port_id_customer],
                                           vlans=[vlan_id_provider1,
                                                  vlan_id_provider2],
                                           tagged='Tagged')

        # Add entries about customer and provider in port table
        env.switch[1].ui.configure_qinq_ports([port_id_provider], mode='ProviderMapped')
        env.switch[1].ui.configure_qinq_ports([port_id_provider], tpid=37120)

        env.switch[1].ui.configure_qinq_ports([port_id_customer], mode='CustomerMapped')
        env.switch[1].ui.configure_qinq_ports([port_id_customer], tpid=33024)

        # Set options for vlan mapping
        env.switch[1].ui.configure_qinq_vlan_mapping([port_id_customer],
                                                     vlan_id_customer1,
                                                     vlan_priority_customer,
                                                     vlan_id_provider1,
                                                     vlan_priority_provider)
        env.switch[1].ui.configure_qinq_vlan_mapping([port_id_customer],
                                                     vlan_id_customer2,
                                                     vlan_priority_customer,
                                                     vlan_id_provider2,
                                                     vlan_priority_provider)

        # Define packets
        packet_definition = ({"Ethernet": {"dst": destination_mac,
                                        "src": source_mac,
                                        "type": 0x9100}},
                             {"Dot1Q": {"vlan": vlan_id_provider1,
                                        "type": 0x0800,
                                        "prio": vlan_priority_provider}},
                             {"IP": {}})
        packet_definition1 = ({"Ethernet": {"dst": destination_mac1,
                                         "src": source_mac1,
                                         "type": 0x9100}},
                              {"Dot1Q": {"vlan": vlan_id_provider2,
                                         "type": 0x0800,
                                         "prio": vlan_priority_provider}},
                              {"IP": {}})

        # Wait some time to add all rows to tables
        time.sleep(1)

        # Start sniffer
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        # Send one packet to the test port.
        stream_id = env.tg[1].set_stream(packet_definition,
                                         count=1,
                                         iface=ports[('tg1', 'sw1')][2])
        stream_id_1 = env.tg[1].set_stream(packet_definition1,
                                           count=1,
                                           iface=ports[('tg1', 'sw1')][2])
        env.tg[1].start_streams([stream_id, stream_id_1])

        data = env.tg[1].stop_sniff(sniff_ports)
        env.tg[1].stop_streams([stream_id, stream_id_1])

        helpers.print_sniffed_data_brief(data)

        # Verify that customer unmapped packet will be received
        # in correct port if it is send provider mapped packet
        assert sniff_ports[0] in list(data.keys()), "No packet on expected port"

        params = [{"layer": "Ethernet", "field": 'dst', "value": destination_mac.lower()}]
        packet = helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                  params=params,
                                                  sniff_data=data,
                                                  tg=env.tg[1])[0]

        assert env.tg[1].check_packet_field(packet=packet, layer="Ethernet", field="type",
                                            value=tp_id_2), "Type field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="vlan",
                                            value=vlan_id_customer1), "Vlan field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="prio",
                                            value=vlan_priority_customer), "Prio field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="type", value=2048), "Type field value isn't equal to expected"

        params = [{"layer": "Ethernet", "field": 'dst', "value": destination_mac1.lower()}]
        packet = helpers.get_packet_from_the_port(sniff_port=sniff_ports[0],
                                                  params=params,
                                                  sniff_data=data,
                                                  tg=env.tg[1])[0]
        assert env.tg[1].check_packet_field(packet=packet, layer="Ethernet", field="type",
                                            value=tp_id_2), "Type field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="vlan",
                                            value=vlan_id_customer2), "Vlan field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="prio",
                                            value=vlan_priority_customer), "Prio field value isn't equal to expected"
        assert env.tg[1].check_packet_field(packet=packet, layer="Dot1Q", field="type", value=2048), "Type field value isn't equal to expected"

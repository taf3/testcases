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

@file test_vlan_samples.py

@summary   Samples for Vlan configuration.

@details
Following test cases are tested:
1. Verify that simple Vlan can be created and deleted.
2. Verify that port can be added to(removed from) Vlan.
3. Verify that traffic is processed according to the configured Vlan.
"""

import pytest

from testlib import helpers


@pytest.mark.vlan
@pytest.mark.simplified
class TestVlanSamples(object):
    """
    @description Suite for Vlan testing
    """

    def test_configure_vlan(self, env):
        """
        @brief  Verify that simple Vlan can be created and deleted
        @steps
            -# Create new Vlan.
            -# Verify Vlan has been created.
            -# Delete new Vlan.
            -# Verify Vlan has been deleted.
        @endsteps
        """
        # Create new Vlan 100
        env.switch[1].ui.create_vlans(vlans=[100, ])

        # Verify that Vlan is created.
        vlan = {'vlanId': 100,
                'name': 'VLAN-100'}
        vlans_table = env.switch[1].ui.get_table_vlans()
        assert vlan in vlans_table, 'Vlan 100 has not been added'

        # Delete created test Vlan.
        env.switch[1].ui.delete_vlans(vlans=[100, ])

        # Verify LAG has been deleted
        vlans_table = env.switch[1].ui.get_table_vlans()
        assert vlan not in vlans_table, 'Vlan 100 has not been deleted'

    def test_configure_vlan_ports(self, env):
        """
        @brief  Verify that port can be added to(removed from) Vlan
        @steps
            -# Create new Vlan.
            -# Add two ports into Vlan
            -# Verify ports have been added to Vlan.
            -# Delete port from Vlan.
            -# Verify port has been deleted from Vlan.
        @endsteps
        """
        # Create new Vlan 100
        env.switch[1].ui.create_vlans(vlans=[100, ])

        # Add ports into the Vlan
        env.switch[1].ui.create_vlan_ports(ports=[1, 2], vlans=[100], tagged='Tagged')

        # Verify ports have been added into the Vlan
        ports_100 = [x['portId'] for x in env.switch[1].ui.get_table_ports2vlans()
                     if x['vlanId'] == 100]
        assert 1 in ports_100, "Port 1 is not in Vlan 100"
        assert 2 in ports_100, "Port 2 is not in Vlan 100"

        # Delete port 1 from Vlan
        env.switch[1].ui.delete_vlan_ports(ports=[1], vlans=[100])

        # Verify ports in Vlan
        ports_100 = [x['portId'] for x in env.switch[1].ui.get_table_ports2vlans()
                     if x['vlanId'] == 100]
        assert 1 not in ports_100, "Port 1 is in Vlan 100"
        assert 2 in ports_100, "Port 2 is not in Vlan 100"

    def test_vlan_traffic(self, env):
        """
        @brief  Verify that traffic is processed according to the configured Vlan
        @steps
            -# Create new Vlan.
            -# Add two ports into Vlan
            -# Send traffic to the first Vlan port.
            -# Verify traffic is forwarded only from second Vlan port.
        @endsteps
        """
        # Get active ports: use four ports for test case
        active_ports = env.get_ports([['tg1', 'sw1', 3], ])
        device_ports = list(active_ports[('sw1', 'tg1')].values())
        sniff_ports = list(active_ports[('tg1', 'sw1')].values())

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, active_ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        # Create new Vlan
        env.switch[1].ui.create_vlans(vlans=[20, ])

        # Add port into the Vlan
        env.switch[1].ui.create_vlan_ports(ports=device_ports[:2],
                                           vlans=[20],
                                           tagged='Untagged')

        # Generate test traffic
        packet = ({"Ethernet": {"dst": "00:00:11:11:11:11", "src": "00:00:02:02:02:02", "type": 0x8100}},
                  {'Dot1Q': {'vlan': 20}},
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

        #Traffic should be forwarded from Vlan ports
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

        # Traffic should not be forwarded from non-Vlan ports
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"

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

@file test_mirroring_samples.py

@summary   Samples for Mirroring configuration.

@details
Following test cases are tested:
1. Verify that simple Mirroring session can be created and deleted.
2. Verify that traffic is processed according to the configured Mirroring session.
"""

import pytest

from testlib import helpers


@pytest.mark.mirroring
@pytest.mark.simplified
class TestMirroringSamples(object):
    """
    @description Suite for Mirroring testing
    """

    def test_configure_mirroring_session(self, env):
        """
        @brief  Verify that simple Mirroring session can be created and deleted
        @steps
            -# Create simple mirroring session.
            -# Verify session has been created.
            -# Delete mirroring session.
            -# Verify session has been deleted.
        @endsteps
        """
        # Create simple mirroring session:
        # mirror all traffic from port 1 to port 2
        env.switch[1].ui.create_mirror_session(1, 2, 'IngressAndEgress')

        # Verify mirroring session has been created
        sessions = env.switch[1].ui.get_mirroring_sessions()

        session = {'sourcePortId': 1,
                   'destinationPortId': 2,
                   'mirroringMode': 'IngressAndEgress'}

        assert session in sessions, 'Mirroring session has not been created'

        # Delete mirroring session
        env.switch[1].ui.delete_mirroring_session(1, 2, 'IngressAndEgress')

        # Verify mirroring session has been deleted
        sessions = env.switch[1].ui.get_mirroring_sessions()
        assert not sessions, 'Mirroring session has not been deleted'

    def test_mirroring_traffic(self, env):
        """
        @brief  Verify that simple Mirroring session can be created and deleted
        @steps
            -# Create simple mirroring session.
            -# Create static Fdb entry
            -# Send traffic that match created Fdb.
            -# Verify traffic is forwarded.
            -# Verify traffic is mirrored.
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

        self.suite_logger.debug("Create Static FDB")
        # Create static Fdb record for second port
        mac = "00:00:00:11:11:11"
        env.switch[1].ui.create_static_macs(port=device_ports[1], vlans=[1], macs=[mac])

        # Create simple mirroring session
        env.switch[1].ui.create_mirror_session(device_ports[0],
                                               device_ports[2],
                                               'IngressAndEgress')

        # Generate test traffic
        packet = ({"Ethernet": {"dst": "00:00:00:11:11:11", "src": "00:00:00:02:02:02", "type": 0x8100}},
                  {"Dot1Q": {"vlan": 1}},
                  {"IP": {}},
                  {"TCP": {}})

        # Send packets to the first port
        stream = env.tg[1].set_stream(packet, count=1, iface=sniff_ports[0])

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify traffic is processed according to the FDB record")
        # Get packets from the captured data
        # Verify first packet is sent only to second port
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:02:02:02'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

        # Verify ingress packet is mirrored
        params_2 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:02:02:02'},
                    {"layer": "Dot1Q", "field": 'vlan', "value": 1}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"


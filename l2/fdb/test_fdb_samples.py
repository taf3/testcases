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
1. Add/Delete static Fdb.
2. Test static Fdb with traffic.
3. Test dynamic Fdb with traffic.
"""

import pytest

from testlib import helpers


@pytest.mark.fdb
@pytest.mark.simplified
class TestFdbSamples(object):
    """
    @description Suite for Fdb testing
    """

    def test_static_fdb(self, env):
        """
        @brief  Add/Delete static Fdb
        @steps
            -# Create static Fdb record.
            -# Verify static Fdb has been created.
            -# Delete static Fdb record.
            -# Verify static Fdb has been deleted.
        @endsteps
        """
        self.suite_logger.debug("Create and Verify Static FDB record")
        # Add static Fdb record
        mac = "00:00:00:11:11:11"
        device_port = env.get_ports([['sw1', 'tg1', 1], ])[('sw1', 'tg1')][1]
        env.switch[1].ui.create_static_macs(port=device_port, vlans=[1], macs=[mac])

        # Verify static Fdb has been created
        fdb_table = env.switch[1].ui.get_table_fdb("Static")
        fdb = {"portId": device_port, "vlanId": 1, "macAddress": mac}
        assert fdb in fdb_table, "Static Fdb {0} was not added".format(fdb)
        # Verify static Fdb record is displayed with all Fdbs
        fdb_table = env.switch[1].ui.get_table_fdb("Fdb")
        fdb["type"] = "Static"
        assert fdb in fdb_table, "Static Fdb {0} was not added".format(fdb)

        self.suite_logger.debug("Delete Static FDB record")
        # Remove static Fdb
        env.switch[1].ui.delete_static_mac(port=device_port, vlan=1, mac=mac)
        # Verify static Fdb has been deleted
        fdb_table = env.switch[1].ui.get_table_fdb("Static")
        del fdb['type']
        assert fdb not in fdb_table, "Static Fdb {0} was not deleted".format(fdb)
        fdb_table = env.switch[1].ui.get_table_fdb("Fdb")
        fdb["type"] = "Static"
        assert fdb not in fdb_table, "Static Fdb {0} was not deleted".format(fdb)

    def test_static_fdb_traffic(self, env):
        """
        @brief  Test static Fdb with traffic.
        @steps
            -# Create static Fdb record.
            -# Send packet that matches create Fdb.
            -# Verify packet is forwarded according to the Fdb.
            -# Send packet that doesn't match create Fdb.
            -# Verify packet is flooded.
        @endsteps
        """
        # Get active ports: use four ports for test case
        active_ports = env.get_ports([['tg1', 'sw1', 4], ])
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

        # Generate test traffic
        packet_1 = ({"Ethernet": {"dst": "00:00:00:11:11:11", "src": "00:00:00:02:02:02"}},
                    {"IP": {}}, {"TCP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:03:03:03", "src": "00:00:00:04:04:04"}},
                    {"IP": {}}, {"TCP": {}})
        # Send packets to the first port
        stream_1 = env.tg[1].set_stream(packet_1, count=1, iface=sniff_ports[0])
        stream_2 = env.tg[1].set_stream(packet_2, count=1, iface=sniff_ports[0])
        streams = [stream_1, stream_2]

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].start_streams(streams)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Stop traffic
        env.tg[1].stop_streams()

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify traffic is processed according to the FDB records")
        # Get packets from the captured data
        # Verify first packet is sent only to second port
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:02:02:02'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[3],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"

        # Verify second packet is flooded
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:03:03:03'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:04:04:04'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[3],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

    def test_dynamic_fdb(self, env):
        """
        @brief  Test dynamic Fdb with traffic
        @steps
            -# Send packet to the device.
            -# Verify Dynamic Fbd has been created using packet's Ethernet.src address
            -# Send packet that matches create Fdb.
            -# Verify packet is forwarded according to the Fdb.
            -# Send packet that doesn't match create Fdb.
            -# Verify packet is flooded.
        @endsteps
        """
        # Get active ports: use four ports for test case
        active_ports = env.get_ports([['tg1', 'sw1', 4], ])
        device_ports = list(active_ports[('sw1', 'tg1')].values())
        sniff_ports = list(active_ports[('tg1', 'sw1')].values())

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, active_ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        self.suite_logger.debug("Configure and send the test traffic")
        # Configure stream for adding dynamic Fdb
        packet = ({"Ethernet": {"src": "00:00:00:11:11:11", "dst": "00:00:00:05:05:05"}},
                  {"IP": {}}, {"TCP": {}})
        stream = env.tg[1].set_stream(packet, count=1, iface=sniff_ports[1])
        env.tg[1].send_stream(stream)
        env.tg[1].stop_streams()

        self.suite_logger.debug("Verify Dynamic FDB is created")
        # Verify Fdb record is added
        fdb_table = env.switch[1].ui.get_table_fdb("Fdb")
        fdb = {"portId": device_ports[1], "vlanId": 1,
               "macAddress": "00:00:00:11:11:11", "type": "Dynamic"}
        assert fdb in fdb_table, "Dynamic Fdb {0} was not added".format(fdb)

        self.suite_logger.debug("Configure the test traffic to match created FDB")
        # Generate test traffic
        packet_1 = ({"Ethernet": {"dst": "00:00:00:11:11:11", "src": "00:00:00:02:02:02"}},
                    {"IP": {}}, {"TCP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:03:03:03", "src": "00:00:00:04:04:04"}},
                    {"IP": {}}, {"TCP": {}})
        # Send packets to the first port
        stream_1 = env.tg[1].set_stream(packet_1, count=1, iface=sniff_ports[0])
        stream_2 = env.tg[1].set_stream(packet_2, count=1, iface=sniff_ports[0])
        streams = [stream_1, stream_2]

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].start_streams(streams)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Stop traffic
        env.tg[1].stop_streams()

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        self.suite_logger.debug("Verify traffic is processed according to the FDB")
        # Get packets from the captured data
        # Verify first packet is sent only to second port
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:02:02:02'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[3],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is received"

        # Verify second packet is flooded
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:03:03:03'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:04:04:04'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[3],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 1, \
            "Packet is not received"

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

@file test_switch.py

@summary   Samples for switch configuration.

@details
Following test cases are tested:
1. Create simple switch configuration.
2. Simple operations with ports
3. Perform special switch operations.
4. Negative switch configuration
"""

import pytest

from testlib import helpers
from testlib.custom_exceptions import SwitchException, UIException

# There are several types of predefined environment:
# simplified: 3-5 links between one switch and traffic generator
# golden: 3 switches connected to each other and to the traffic generator
# diamond: 4 switches connected to each other and to traffic generator
# standalone: one switch without other connections.

# Environment marker used for test filtering, e.g.
# Use "-m 'simplified'" in the command line to execute tests on simplified environment


@pytest.mark.simplified
class TestSwitchSamples(object):
    """
    @description Suite for switch configuration
    """

    # Each test case should have 'env' argument related
    # to the 'env' fixture responsible for test environment
    def test_switch_configuration(self, env):
        """
        @brief  Add simple switch configuration
        """
        self.suite_logger.debug("Create simple switch configuration (Static FDB record)")
        # Add static Fdb record
        # Use env.switch[1].ui.* methods in order to set/get switch configuration
        mac_1 = "00:00:00:11:11:11"
        mac_2 = "00:00:00:22:22:22"
        # Create Static FDBs with macs mac_1 and mac_2 for port 1 on vlan 1
        env.switch[1].ui.create_static_macs(port=1, vlans=[1], macs=[mac_1, mac_2])

        # Verify static Fdbs have been created
        fdb_table = env.switch[1].ui.get_table_fdb("Static")
        # Each record in Static FDB table has the following representation:
        # {"portId": PortID, "vlanId": VlanID, "macAddress": MAC}
        fdb_1 = {"portId": 1, "vlanId": 1, "macAddress": mac_1}
        # Use assertion with error message
        # This error message is displayed as failure reason
        assert fdb_1 in fdb_table, "Static Fdb {0} was not added".format(fdb_1)
        fdb_2 = {"portId": 1, "vlanId": 1, "macAddress": mac_2}
        assert fdb_2 in fdb_table, "Static Fdb {0} was not added".format(fdb_2)
        # Verify static Fdb records are displayed with all FDBs
        fdb_table = env.switch[1].ui.get_table_fdb("Fdb")
        # Each record in FDB table has the following representation:
        # {"portId": PortID, "vlanId": VlanID, "macAddress": MAC, "type": "Static"/"Dynamic"}
        fdb_1["type"] = "Static"
        assert fdb_1 in fdb_table, "Static Fdb {0} was not added".format(fdb_1)
        fdb_2["type"] = "Static"
        assert fdb_2 in fdb_table, "Static Fdb {0} was not added".format(fdb_2)

        self.suite_logger.debug("Delete Static FDB record")
        # Remove static Fdb
        env.switch[1].ui.delete_static_mac(port=1, vlan=1, mac=mac_1)
        # Verify static Fdb has been deleted from FDB table
        fdb_table = env.switch[1].ui.get_table_fdb("Fdb")
        assert fdb_1 not in fdb_table, "Static Fdb {0} was not deleted".format(fdb_1)
        assert fdb_2 in fdb_table, "Static Fdb {0} was not added".format(fdb_2)

        fdb_table = env.switch[1].ui.get_table_fdb("Static")
        del fdb_1['type']
        assert fdb_1 not in fdb_table, "Static Fdb {0} was not deleted".format(fdb_1)
        del fdb_2['type']
        assert fdb_2 in fdb_table, "Static Fdb {0} was not added".format(fdb_2)

    def test_switch_ports_operations(self, env):
        """
        @brief  Simple operations with ports.
        """
        # Get active ports.
        # JSON setup file contain info about links between devices
        # env.get_ports - returns dictionary of ports in format
        # {link_key: ports_dict}
        # where
        # link_key is a list of device's acronymes
        # ports_dict contains real port names (IDs) from JSON file
        # Example:
        # {('sw1', 'tg1'): {1: 24, 2: 25}, ('tg1', 'sw1'): {1: 'eth1', 2: 'eth2'}}
        # where switch's port 24 is connected to the traffic generator's port 'eth1', etc.

        # Get 4 links between switch and tg
        active_ports = env.get_ports([['tg1', 'sw1', 4], ])

        # Disable all ports and enabling only necessary ports:

        # helpers module contains special methods to operate with ports
        # Set all switch ports into Admin Down state
        # in order to omit traffic from other connections
        helpers.set_all_ports_admin_disabled(env.switch)

        # Enable only links used in current test case
        helpers.set_ports_admin_enabled(env.switch, active_ports)

        self.suite_logger.debug("Create Static FDB")
        # Create static Fdb record for second port in configuration
        mac = "00:00:00:11:11:11"
        # Get second port of device
        port_2 = active_ports[('sw1', 'tg1')][2]
        env.switch[1].ui.create_static_macs(port=port_2, vlans=[1], macs=[mac])

        # Generate test traffic
        packet_1 = ({"Ethernet": {"dst": "00:00:00:11:11:11", "src": "00:00:00:02:02:02"}},
                    {"IP": {}}, {"TCP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:03:03:03", "src": "00:00:00:04:04:04"}},
                    {"IP": {}}, {"TCP": {}})
        # Send packets to the first port
        # Get first port of TG
        port_tg_2 = active_ports[('tg1', 'sw1')][1]
        stream_1 = env.tg[1].set_stream(packet_1, count=1, iface=port_tg_2)
        stream_2 = env.tg[1].set_stream(packet_2, count=1, iface=port_tg_2)
        streams = [stream_1, stream_2]

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        # Configure ports for capture (get all TG ports
        sniff_ports = list(active_ports[('tg1', 'sw1')].values())
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].start_streams(streams)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Stop traffic
        env.tg[1].stop_streams(streams)

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

    def test_switch_special_operations(self, env):
        """
        @brief  Perform special switch operations
        """

        # Clear switch configuration using UI call
        # This call will clear device's configuration
        self.suite_logger.debug("Clear configuration with ui.clear_config")
        env.switch[1].ui.clear_config()

        # Clear switch configuration using switch 'clearconfig' method
        # This call will clear device's configuration using UI command
        # and apply syslog and port pre-configurations
        self.suite_logger.debug("Clear configuration with clearconfig")
        env.switch[1].clearconfig()

        # Clear switch configuration using switch 'cleanup' method
        # This call will check device's status
        # and clear configuration using 'clearconfig' method
        self.suite_logger.debug("Clear configuration with cleanup")
        env.switch[1].cleanup()

        # Stop the device
        self.suite_logger.debug("Stop the device")
        env.switch[1].stop()

        # Start the device
        self.suite_logger.debug("Start the device")
        env.switch[1].start()

        # Wait for device become available
        self.suite_logger.debug("Get the device")
        env.switch[1].get()

        # Restart the device using powercycle
        self.suite_logger.debug("Restart the device using powercycle")
        env.switch[1].restart(mode='powercycle')

        # Restart the device using UI
        self.suite_logger.debug("Restart the device using UI command")
        env.switch[1].restart(mode='ui')

    def test_negative_configuration(self, env):
        """
        @brief  Negative switch configuration
        """
        self.suite_logger.debug("Add wrong Fdb entry")

        mac = '00:00:00:00:11:11:11'

        # For negative configuration use try/except clause
        # with expected SwitchException, UIException or AssertionError
        try:
            env.switch[1].ui.create_static_macs(port=1, vlans=[1], macs=[mac])
            pytest.fail("Wrong Fdb has been configured")
        except (SwitchException, UIException, AssertionError):
            pass

        # or use ui_raises from test_common.ui_helpers module
        env.switch[1].ui.ui_raises('create_static_macs', port=1, vlans=[1], macs=[mac])
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

@file test_switch_ons.py

@summary   Samples for ONS switch configuration.

@details
Following test cases are tested:
1. Create simple switch configuration using XMLRPC wrappers.
2. Create simple switch configuration using direct XMLRPC calls
"""

import pytest

from testlib import helpers


@pytest.mark.simplified
@helpers.run_on_ui(["ons_xmlrpc"], "Execute test cases only using XMLRPC UI")
class TestSwitchSamples(object):
    """
    @description Suite for switch configuration
    """

    def test_switch_xmlrpc_wrappers(self, env):
        """
        @brief  Create simple switch configuration using XMLRPC wrappers
        """
        self.suite_logger.debug("Create simple switch configuration (Static FDB record)")
        # Add static Fdb record
        # Use env.switch[1].setprop_row methods in order to
        # perform nb.TABLE_NAME.addRow XMLRPC call
        # env.switch.setprop_row(TABLE_NAME, ENTRY)
        mac = "00:00:00:11:11:11"
        # Create Static FDBs with macs "00:00:00:11:11:11" for port 2 on vlan 1
        env.switch[1].setprop_row('StaticMAC', (mac, 1, 2))

        # Verify static Fdb has been created
        # USe env.switch[1].getprop_table(TABLE_NAME) in order to
        # perform nb.TABLE_NAME.getTable() XMLRPC call
        fdb_table = env.switch[1].getprop_table("StaticMAC")
        # Each record in Static FDB table has the following representation:
        # {"portId": PortID, "vlanId": VlanID, "macAddress": MAC}
        fdb_1 = {"portId": 2, "vlanId": 1, "macAddress": mac}
        # Use assertion with error message
        # This error message is displayed as failure reason
        assert fdb_1 in fdb_table, "Static Fdb {0} was not added".format(fdb_1)

        # Get specific entry
        # Use env.switch[1].getprop_row(TABLE_NAME, row_Id) in order to
        # perform nb.TABLE_NAME.getRow(row_Id) XMLRPC call
        fdb = env.switch[1].getprop_row('StaticMAC', 1)
        self.suite_logger.debug(fdb)

        # Get specific value
        # Use env.switch[1].getprop(TABLE_NAME, param_name, row_Id) in order to
        # perform nb.TABLE_NAME.get.param_name(row_Id) XMLRPC call
        mac_1 = env.switch[1].getprop('StaticMAC', 'macAddress', 1)
        assert mac == mac_1

        # Get table size
        # Use env.switch[1].getprop_size(TABLE_NAME) in order to
        # perform nb.TABLE_NAME.getSize() XMLRPC call
        size = env.switch[1].getprop_size('StaticMAC')
        assert size == 1

        # Change specific value
        # Use env.switch[1].setprop(TABLE_NAME, param_name, (row_Id, new_value)) in
        # order to perform nb.TABLE_NAME.set.param_name(row_Id, new_value) XMLRPC call
        env.switch[1].setprop('StaticMAC', 'portId', (1, 3))

        # Find specific entry
        # Use env.switch[1].findprop(TABLE_NAME, *values) in order to
        # perform nb.TABLE_NAME.find(*values) XMLRPC call
        row_Id = env.switch[1].findprop('StaticMAC', ['00:00:00:11:11:11', 1])
        assert row_Id == 1

        # Delete specific entry
        # Use env.switch[1].delprop_row(TABLE_NAME, row_Id) in order to
        # perform nb.TABLE_NAME.delRow(row_Id) XMLRPC call
        env.switch[1].delprop_row('StaticMAC', row_Id)

    def test_switch_direct_xmlrpc_calls(self, env):
        """
        @brief  Create simple switch configuration using direct XMLRPC calls
        """
        self.suite_logger.debug("Create simple switch configuration (Static FDB record)")
        # Add static Fdb record
        # Use env.switch[1].xmlproxy.* in order to
        # perform direct XMLRPC call

        mac = "00:00:00:11:11:11"
        # Create Static FDBs with macs "00:00:00:11:11:11" for port 2 on vlan 1
        env.switch[1].xmlproxy.nb.StaticMAC.addRow(mac, 1, 2)

        # Verify static Fdb has been created
        fdb_table = env.switch[1].xmlproxy.nb.StaticMAC.getTable()

        fdb_1 = {"portId": 2, "vlanId": 1, "macAddress": mac}
        assert fdb_1 in fdb_table, "Static Fdb {0} was not added".format(fdb_1)

        # Get specific entry
        fdb = env.switch[1].xmlproxy.nb.StaticMAC.getRow(1)
        self.suite_logger.debug(fdb)

        # Get specific value
        mac_1 = env.switch[1].xmlproxy.nb.StaticMAC.get.macAddress(1)
        assert mac == mac_1

        # Get table size
        size = env.switch[1].xmlproxy.nb.StaticMAC.size()
        assert size == 1

        # Change specific value
        env.switch[1].xmlproxy.nb.StaticMAC.set.portId(1, 3)

        # Find specific entry
        row_Id = env.switch[1].xmlproxy.nb.StaticMAC.find('00:00:00:11:11:11', 1)
        assert row_Id == 1

        # Delete specific entry
        # Use env.switch[1].delprop_row(TABLE_NAME, row_Id) in order to
        # perform nb.TABLE_NAME.delRow(row_Id) XMLRPC call
        env.switch[1].xmlproxy.nb.StaticMAC.delRow(row_Id)
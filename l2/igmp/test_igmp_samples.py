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

@file test_igmp_samples.py

@summary   Samples for IGMP configuration.

@details
Following test cases are tested:
1. Verify that a multicast traffic is received only on the port where Group is registered.
"""

import time

import pytest

from testlib import helpers


@pytest.mark.igmp
@pytest.mark.simplified
class TestIGMPSamples(object):
    """
    @description Suite for IGMP testing
    """

    # Attributes and Properties

    def wait_until_entry_is_expired(self, expected_timeout=1,
                                    switch_instance=None, table_name="L2Multicast"):
        """
        @brief  wait until entry is expired from table

        @param  switch_instance:  Switch class instance to work with
        @type  switch_instance:  SwitchGeneral
        @param  expected_timeout:  Time to wait
        @type  expected_timeout:  int

        @return  True or raise exception
        @rtype: True

        @par  Example:
        @code
        assert self.wait_until_entry_is_expired(timeout=10, switch_instance=env.switch[2])
        @endco
        """
        default_interval = switch_instance.ui.get_table_igmp_snooping_global_admin(
            param="queryInterval")
        default_robustness = switch_instance.ui.get_table_igmp_snooping_global_admin(
            param="querierRobustness")
        min_querier_robustness = 1
        max_response_time = 10
        switch_instance.ui.configure_igmp_global(
            querier_robustness=min_querier_robustness)
        if expected_timeout <= 10:
            switch_instance.ui.configure_igmp_global(query_interval=1)
        else:
            switch_instance.ui.configure_igmp_global(
                query_interval=expected_timeout - max_response_time)
        # aging timeout is determined by the formula (queryInterval * querierRobustness) + (maxResponseTime) (+1 it is acceptable error)
        timeout = (
            switch_instance.ui.get_table_igmp_snooping_global_admin(param="queryInterval") +
            switch_instance.ui.get_table_igmp_snooping_global_admin(
                param="querierRobustness") + max_response_time)

        # Get L2Multicast table
        table = switch_instance.ui.get_table_l2_multicast()
        # if table is not empty wait during the calculated timeout
        if table:
            time.sleep(timeout)
            table = switch_instance.ui.get_table_l2_multicast()
        self.suite_logger.debug("%s table for switch is :%s" % (table_name, table))

        # Verify table is empty
        try:
            assert not table
        except AssertionError:
            pytest.fail("Table %s is not empty." % table_name)
        else:
            return True
        finally:
            switch_instance.ui.configure_igmp_global(query_interval=default_interval)
            switch_instance.ui.configure_igmp_global(
                querier_robustness=default_robustness)

    def is_row_added_to_l2multicast_table(self, mac_address=None,
                                          port_id=None, vlan_id=1, switch_instance=None):
        """
        @brief Check if row with specified parameters added to L2Multicast table.

        @param  mac_address:  Multicast MAC
        @type  mac_address:  str
        @param  port_id:  portID
        @type  port_id:  int
        @param  vlan_id:  vlanID
        @type  vlan_id:  int
        @param  switch_instance:  Switch class instance to work with
        @type  switch_instance:  SwitchGeneral

        @return  True or False
        @rtype: bool
        """
        # Need to wait untill entry will be added to L2Multicast table.
        time.sleep(1)
        table = switch_instance.ui.get_table_l2_multicast()
        for row in table:
            if row['macAddress'] == mac_address and row['portId'] == port_id and row['vlanId'] == vlan_id:
                return True
        return False

    # Test Cases
    @pytest.mark.skip("Pypacker does not work properly with IP Options field and IGMP layer")
    def test_sending_multicast_traffic(self, env):
        """
        @brief  Verify that a multicast traffic is received only on the port where
                Group is registered.
        @note  If a switch receives an unregistered packet, it must forward that packet
                on all ports to which an IGMP router is attached.
        @steps
            -# Enable IGMP globally.
            -# Enable IGMP on port 1, port 2 and port 3.
            -# Send packet to port 1.
            -# Send IGMP Report to port 2.
            -# Verify that multicast forwarding entry is added to L2Multicast table.
            -# Send packet to port 1.
            -# Verify that sent packet is forwarded from port 2.
        @endsteps
        """
        # Test variables
        mcast_address = "01:00:5E:00:01:05"  # Multicast MAC address
        r_srs_address = "00:00:02:03:04:05"  # Reporter SRC MAC address
        group_address = "224.0.1.5"  # Group IP address

        # Define active ports
        ports = env.get_ports([['tg1', 'sw1', 3], ])

        port_1 = ports[('sw1', 'tg1')][1]
        port_2 = ports[('sw1', 'tg1')][2]
        port_3 = ports[('sw1', 'tg1')][3]

        # Disable all ports and enabling only necessary ones:
        helpers.set_all_ports_admin_disabled(env.switch)
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Disable STP.")
        env.switch[1].ui.configure_spanning_tree(enable='Disabled')

        self.suite_logger.debug("Enable IGMP globally.")
        env.switch[1].ui.configure_igmp_global(mode='Enabled')

        # Enable IGMP on ports.
        self.suite_logger.debug("Enable IGMP on ports.")
        env.switch[1].ui.configure_igmp_per_ports([port_1, port_2, port_3],
                                                  mode='Enabled')

        # Clearing L2Multicast table.
        self.wait_until_entry_is_expired(switch_instance=env.switch[1])

        # Define ports for sniffing
        sniff_ports = list(ports[('tg1', 'sw1')].values())

        self.suite_logger.debug("Start sniffer.")
        env.tg[1].start_sniff(sniff_ports, sniffing_time=3)

        self.suite_logger.debug("Send packet to port 1.")
        packet_definition = ({"Ethernet": {"dst": mcast_address,
                                        "src": r_srs_address,
                                        "type": 0x0800}},
                             {"IP": {"src": "10.10.10.10",
                                     "dst": group_address,
                                     "p": 17}},
                             {"UDP": {}})
        stream_id_1 = env.tg[1].set_stream(packet_definition,
                                           count=1,
                                           iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id_1)

        self.suite_logger.debug("Stop sniffer.")
        data = env.tg[1].stop_sniff(sniff_ports)

        self.suite_logger.debug("Verify that packet is not forwarded.")
        helpers.is_packet_received(data=data, iface_1=sniff_ports[2],
                                   value_1=mcast_address.lower(), layer_2="Ethernet",
                                   field_2="src", value_2=r_srs_address,
                                   tg_instance=env.tg[1], result=False)
        helpers.is_packet_received(data=data, iface_1=sniff_ports[1],
                                   value_1=mcast_address.lower(), layer_2="Ethernet",
                                   field_2="src", value_2=r_srs_address,
                                   tg_instance=env.tg[1], result=False)

        self.suite_logger.debug("Send IGMP membership Report to port 2.")
        igmp_report_v2 = ({"Ethernet": {"dst": mcast_address,
                                     "src": r_srs_address,
                                     "type": 0x0800}},
                          {"IP": {"src": "10.10.10.10",
                                  "dst": group_address,
                                  "p": 2,
                                  "ttl": 1,
                                  "opts": [{"IPOption_Router_Alert": {"length": 4}}, ],
                                  "tos": 0xc0,
                                  "len": 32}},
                          {"IGMP": {"type": 0x16,
                                    "gaddr": group_address,
                                    "mrtime": 100}})
        stream_id_1 = env.tg[1].set_stream(igmp_report_v2,
                                           count=1,
                                           iface=ports[('tg1', 'sw1')][2])
        env.tg[1].send_stream(stream_id_1)

        self.suite_logger.debug("Verify that multicast group is added.")
        assert self.is_row_added_to_l2multicast_table(mac_address=mcast_address,
                                                      port_id=port_2,
                                                      switch_instance=env.switch[1]), \
            "Multicast entry is not added"

        self.suite_logger.debug("Start sniffer.")
        env.tg[1].start_sniff(sniff_ports, sniffing_time=3)

        self.suite_logger.debug("Send packet to port 1.")
        stream_id_1 = env.tg[1].set_stream(packet_definition,
                                           count=1,
                                           iface=ports[('tg1', 'sw1')][1])
        env.tg[1].send_stream(stream_id_1)

        self.suite_logger.debug("Stop sniffer.")
        data = env.tg[1].stop_sniff(sniff_ports)

        self.suite_logger.debug("Verify that packet is forwarded from port 2.")
        helpers.is_packet_received(data=data, iface_1=sniff_ports[1],
                                   value_1=mcast_address.lower(), layer_2="Ethernet",
                                   field_2="src", value_2=r_srs_address,
                                   tg_instance=env.tg[1])
        helpers.is_packet_received(data=data, iface_1=sniff_ports[2],
                                   value_1=mcast_address.lower(), layer_2="Ethernet",
                                   field_2="src", value_2=r_srs_address,
                                   tg_instance=env.tg[1], result=False)

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

@file test_statistics_samples.py

@summary   Samples for Statistics configuration.

@details
Following test cases are tested:
1. Verify that proper Statistics value updated during specific traffic is processed

"""

import time

import pytest

from testlib import helpers


@pytest.mark.statistics
@pytest.mark.simplified
class TestStatisticsSamples(object):
    """
    @description Suite for Statistics testing
    """

    def test_statistics(self, env):
        """
        @brief  Verify that proper Statistics value updated during specific traffic is processed
        @steps
            -# Clear all statistics.
            -# Send 100 unicast frames.
            -# Verify proper Statistics values.
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

        # Generate test traffic
        packet = ({"Ethernet": {"dst": "00:00:11:11:11:11", "src": "00:00:02:02:02:02"}},
                  {"IP": {}},
                  {"TCP": {}})

        # Send packets to the second port
        stream = env.tg[1].set_stream(packet, count=100, iface=sniff_ports[1])

        # Clear all Statistics
        env.switch[1].ui.clear_statistics()

        # Get initial Statistics values
        port_0_tx = env.switch[1].ui.get_table_statistics(port=device_ports[0],
                                                          stat_name='IfOutUcastPkts')
        port_1_rx = env.switch[1].ui.get_table_statistics(port=device_ports[1],
                                                          stat_name='IfInUcastPkts')
        port_2_tx = env.switch[1].ui.get_table_statistics(port=device_ports[2],
                                                          stat_name='IfOutUcastPkts')

        self.suite_logger.debug("Send the test traffic")
        env.tg[1].send_stream(stream)

        # Wait for Statistics to be updated
        time.sleep(15)

        # Get Statistics
        port_0_tx_end = env.switch[1].ui.get_table_statistics(port=device_ports[0],
                                                              stat_name='IfOutUcastPkts')
        port_1_rx_end = env.switch[1].ui.get_table_statistics(port=device_ports[1],
                                                              stat_name='IfInUcastPkts')
        port_2_tx_end = env.switch[1].ui.get_table_statistics(port=device_ports[2],
                                                              stat_name='IfOutUcastPkts')

        # Verify Statistics values
        assert int(port_1_rx_end) - int(port_1_rx) == 100, 'Rx Statistics is wrong'
        assert int(port_0_tx_end) - int(port_0_tx) == 100, 'Tx Statistics is wrong'
        assert int(port_2_tx_end) - int(port_2_tx) == 100, 'Tx Statistics is wrong'
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

@file test_port_configuration_samples.py

@summary   Samples for Port Configuration configuration.

@details
Following test cases are tested:
1. Verify that port configuration can be changed.
"""

import pytest


@pytest.mark.ports
@pytest.mark.simplified
class TestPortConfigSamples(object):
    """
    @description Suite for Port Configuration testing
    """

    def test_port_configuration(self, env):
        """
        @brief  Verify that port configuration can be changed
        @steps
            -# Get Ports table.
            -# Get Port configuration.
            -# Change Port configuration.
            -# Verify Port configuration has been changed.
        @endsteps
        """
        self.suite_logger.debug("Get Ports table")
        ports = env.switch[1].ui.get_table_ports()

        # Print Ports table
        self.suite_logger.debug("Ports table: {}".format(ports))

        # Get Port info
        port_1 = env.switch[1].ui.get_table_ports([1], all_params=True)

        # Print Port info
        self.suite_logger.debug("Port info: {}".format(port_1))

        # Change port configuration:
        # adminMode, macAddress, autoNegotiate, speed, duplex, flowControl,
        # maxFrameSize, pvid, pvpt, ingressFiltering, discardMode, cutThrough, appError
        env.switch[1].ui.modify_ports([1], maxFrameSize=2000)

        # Verify Port configuration has been changed
        assert env.switch[1].ui.get_table_ports([1], all_params=True)[0]['maxFrameSize'] == 2000, \
            "maxFrameSize value has not been changed"

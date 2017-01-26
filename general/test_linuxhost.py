"""
@copyright Copyright (c) 2017, Intel Corporation.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@file test_linuxhost.py

@summary  Samples for linux host simple configuration.

@details
Following test cases are tested:
1. Verify that sample linux host object is existed.
2. Verify that current date can be received via get_current_date and cli_send_command methods.
"""

import pytest


@pytest.mark.lhost_sample
class TestLinuxHostSample(object):
    """
    @description Suite for sample Linux host testing
    """

    # Each test case should have 'env' argument related
    # to the 'env' fixture responsible for test environment
    def test_linuxhost_is_existed(self, env):
        """
        @brief  Verify that sample linuxhost object is existed
        """
        self.suite_logger.debug("Verify that sample Linuxhost is existed")
        assert env.lhost

    def test_linuxhost_cli_methods(self, env):
        """
        @brief  Verify that current date can be received via get_current_date and cli_send_command methods
        """
        self.suite_logger.debug("Get date format via CLI command")
        # Define output date format
        date_format = '+%Y-%m-%d %T'
        # Run CLI command to get current date
        cli_current_date = env.lhost[1].ui.cli_send_command("date '{0}'".format(date_format)).stdout
        # Verify that linux host get_current_date and CLI methods return the same date.
        assert env.lhost[1].ui.get_current_date(date_format=date_format) == cli_current_date.strip()

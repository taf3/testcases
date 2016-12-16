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

@file  conftest.py

@summary  Py.test configuration for test suites.
"""

import pytest

from testlib import loggers
from testlib import fixtures

from os import path as os_path
from os import getpid as os_getpid


# Load necessary plugins from taf/plugins folder
pytest_plugins = [
    "plugins.pytest_reportingserver",  # reporting functionality
    "plugins.pytest_returns",  # returns values instead of PASS
    "plugins.pytest_multiple_run",  # execute test cases several times
    "plugins.pytest_start_from_case",  # start execution from the specified test
    "plugins.pytest_onsenv",  # initialize environment
    "plugins.pytest_skip_filter",  # remove skipped tests from run
    "plugins.pytest_random_collection",  # execute one test (random) from test suite
]


# Add options for logging
def pytest_addoption(parser):
    """
    @brief  TAF specific options
    """
    parser.addoption("--loglevel", action="store", default="INFO",
                     help="Logging level, '%default' by default.")
    parser.addoption("--logdir", action="store", default=None,
                     help="Logging directory path, %default by default.")
    parser.addoption("--silent", action="store_true", default=False,
                     help="Suppress stdout messages. %default by default.")


# Configure pytest logging
def pytest_configure(config):
    config.ctlogger = loggers.module_logger("conftest")
    if config.option.logdir is not None:
        # Set file name of pytest log.
        if config.option.resultlog is None:
            log_suffix = "-".join([config.option.markexpr.replace(" ", "_"),
                                   config.option.keyword.replace(" ", "_")])
            self_pid = str(os_getpid())
            resultlog_name = ".".join(["pytest", log_suffix, self_pid, "log"])
            config.option.resultlog = os_path.join(os_path.expandvars(os_path.expanduser(config.option.logdir)),
                                                   resultlog_name)


# Configure tests logging
@pytest.fixture(scope="class", autouse=True)
def autolog(request):
    """ @brief Inject logger object to test class. """
    return fixtures.autolog(request)

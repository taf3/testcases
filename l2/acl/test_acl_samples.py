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

@file test_acl_samples.py

@summary   Samples for ACL configuration.

@details
Following test cases are tested:
1. Add simple ACL configuration.
2. Add/Delete simple ACLs.
3. Simple ACL test with traffic.
4. ACL Statistics.
"""

import time

import pytest

from testlib import helpers


@pytest.mark.acl
@pytest.mark.simplified
class TestAclSamples(object):
    """
    @description Suite for ACL testing
    """

    def test_acl_configuration(self, env):
        """
        @brief  Add simple ACL configuration
        @steps
            -# Create ACL Expression for Ethernet.dst=00:00:00:01:01:01 .
            -# Verify ACL Expression has been created.
            -# Create "Drop" ACL Action.
            -# Verify ACL Action has been created.
            -# Create ACL Rule for created Expression and Action.
            -# Verify ACL Rule has been created.
        @endsteps
        """
        # Create ACL Expression
        self.suite_logger.debug("Create and Verify ACL Expression")
        expressions = [(1, 'DstMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:01:01:01'), ]
        env.switch[1].ui.create_acl(expressions=expressions)
        # Verify ACL Expression
        expression = env.switch[1].ui.get_table_acl("ACLExpressions")[0]
        assert expression['data'] == '00:00:00:01:01:01'
        assert expression['mask'] == 'FF:FF:FF:FF:FF:FF'
        assert expression['expressionId'] == 1
        assert expression['field'] == 'DstMac'

        # Create ACL Actions
        self.suite_logger.debug("Create and Verify ACL Action")
        actions = [(1, 'Drop', ''), ]
        env.switch[1].ui.create_acl(actions=actions)
        # Verify ACL Action
        action = env.switch[1].ui.get_table_acl("ACLActions")[0]
        assert action['action'] == 'Drop'
        assert action['param'] == ''
        assert action['actionId'] == 1

        # Create ACL Rule
        self.suite_logger.debug("Create and Verify ACL Rule")
        rules = [(1, 1, 1, 'Ingress', 'Enabled', 0), ]
        # Note: ACL Rule should be assigned to ports
        env.switch[1].ui.create_acl(ports=[1, ], rules=rules)
        # Verify ACL Rule
        rule = env.switch[1].ui.get_table_acl("ACLRules")[0]
        assert rule['ruleId'] == 1
        assert rule['expressionId'] == 1
        assert rule['actionId'] == 1
        assert rule['stage'] == 'Ingress'
        assert rule['enabled'] == 'Enabled'
        assert rule['priority'] == 0

    def test_delete_acl(self, env):
        """
        @brief  Add/Delete simple ACL
        @steps
            -# Configure 2 ACL Expressions.
            -# Verify Expressions have been created.
            -# Delete second ACL Expression.
            -# Verify ACL has been deleted.
            -# Configure 2 ACL Actions.
            -# Verify Actions have been created.
            -# Delete second ACL Action.
            -# Verify ACL has been deleted.
            -# Configure ACL Rule.
            -# Verify Rule has been created.
            -# Delete ACL Rule.
            -# Verify ACL has been deleted.
        @endsteps
        """
        # Create ACL Expressions
        self.suite_logger.debug("Create ACL Expressions")
        expressions = [(1, 'DstMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:01:01:01'),
                       (2, 'SrcMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:02:02:02')]
        env.switch[1].ui.create_acl(expressions=expressions)
        # Verify ACL Expression
        expressions_table = env.switch[1].ui.get_table_acl("ACLExpressions")
        # Verify first expression has been added
        expr_1 = {"expressionId": expressions[0][0],
                  "field": expressions[0][1],
                  "mask": expressions[0][2],
                  "data": expressions[0][3]
                  }
        assert expr_1 in expressions_table, \
            "Expression {0} was not added".format(expressions[0])
        # Verify second expression has been added
        expr_2 = {"expressionId": expressions[1][0],
                  "field": expressions[1][1],
                  "mask": expressions[1][2],
                  "data": expressions[1][3]
                  }
        assert expr_2 in expressions_table,\
            "Expression {0} was not added".format(expressions[1])
        # Delete Expression
        self.suite_logger.debug("Delete ACL Expression")
        env.switch[1].ui.delete_acl(expression_ids=[(2, 'SrcMac'), ])
        # Verify Expression has been deleted
        expressions_table = env.switch[1].ui.get_table_acl("ACLExpressions")
        assert expr_2 not in expressions_table, \
            "Expression {0} was not deleted".format(expressions[1])

        # Create ACL Actions
        self.suite_logger.debug("Create ACL Actions")
        actions = [(1, 'Drop', ''),
                   (2, 'Count', '')]
        env.switch[1].ui.create_acl(actions=actions)
        # Verify ACL Action
        actions_table = env.switch[1].ui.get_table_acl("ACLActions")
        # Verify first action has been added
        act_1 = {"actionId": actions[0][0],
                 "action": actions[0][1],
                 "param": actions[0][2]
                 }
        assert act_1 in actions_table, "Action {0} was not added".format(actions[0])
        # Verify second action has been added
        act_2 = {"actionId": actions[1][0],
                 "action": actions[1][1],
                 "param": actions[1][2]
                 }
        assert act_2 in actions_table, "Action {0} was not added".format(actions[1])
        # Delete Action
        self.suite_logger.debug("Delete ACL Action")
        env.switch[1].ui.delete_acl(action_ids=[(2, 'Count'), ])
        # Verify Action has been deleted
        actions_table = env.switch[1].ui.get_table_acl("ACLActions")
        assert act_2 not in actions_table, "Action {0} was not deleted".format(actions[1])

        # Create ACL Rule
        self.suite_logger.debug("Create ACL Rule")
        rules = [(1, 1, 1, 'Ingress', 'Enabled', 0), ]
        env.switch[1].ui.create_acl(ports=[1, ], rules=rules)
        # Verify ACL Rule has been added
        rules_table = env.switch[1].ui.get_table_acl("ACLRules")
        rule = {"ruleId": rules[0][0],
                "expressionId": rules[0][1],
                "actionId": rules[0][2],
                "stage": rules[0][3],
                "enabled": rules[0][4],
                "priority": rules[0][5]
                }
        assert rule in rules_table, "Rule {0} was not added".format(rules[0])
        # Delete Rule
        self.suite_logger.debug("Delete ACL Rule")
        env.switch[1].ui.delete_acl(ports=[1, ], rule_ids=[1, ])
        # Verify Rule has been deleted
        rules_table = env.switch[1].ui.get_table_acl("ACLRules")
        assert rule not in rules_table, "Rule {0} was not deleted".format(rules[0])

    def test_acl_traffic(self, env):
        """
        @brief Simple ACL test with traffic
        @steps
            -# Configure ACL: drop all packets.
            -# Configure ACL: allow packets with Ethernet.dst=00:00:00:01:01:01.
            -# Create stream with Ethernet.dst=00:00:00:01:01:01.
            -# Create stream with Ethernet.dst=00:00:00:03:03:03.
            -# Send streams.
            -# Verify first stream is flooded.
            -# Verify second stream is discarded.
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

        # Configure ACL: drop all packets;
        # allow only packets with Ethernet.dst=00:00:00:01:01:01
        # Configure ACL Expression in format (id, expression, mask, value)
        self.suite_logger.debug("Create ACLs")
        expressions = [(1, 'SrcMac', '00:00:00:00:00:00', '00:00:00:00:00:00'),
                       (2, 'DstMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:01:01:01')]

        # Configure ACL Action in format (id, action, params)
        actions = [(1, 'Drop', ''), (2, 'Allow', '')]

        # Configure ACL Rule in format
        # (id, expression_id, action_id, stage, enabled, priority)
        rules = [(1, 1, 1, 'Ingress', 'Enabled', 0), (2, 2, 2, 'Ingress', 'Enabled', 0)]

        # Create ACLs on device's ports
        try:
            env.switch[1].ui.create_acl(ports=device_ports, expressions=expressions,
                                        actions=actions, rules=rules)

        except Exception as err:
            # Exception in configuration
            self.suite_logger.debug('ACL configuration failed: %s' % err)
            pytest.fail('ACL configuration failed')

        # Wait some time for proper switch behavior
        time.sleep(1)

        # Generate test traffic
        packet_1 = ({"Ethernet": {"dst": "00:00:00:01:01:01", "src": "00:00:00:02:02:02"}},
                    {"IP": {}}, {"TCP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:03:03:03", "src": "00:00:00:04:04:04"}},
                    {"IP": {}}, {"TCP": {}})
        # Send packets to the first port
        stream_1 = env.tg[1].set_stream(packet_1, count=1, iface=sniff_ports[0])
        stream_2 = env.tg[1].set_stream(packet_2, count=1, iface=sniff_ports[0])
        streams = [stream_1, stream_2]

        # Start capture
        self.suite_logger.debug("Start the capture and send the test traffic")
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].start_streams(streams)

        # Stop capture
        data = env.tg[1].stop_sniff(sniff_ports)

        # Stop traffic
        env.tg[1].stop_streams()

        # Print captured data
        helpers.print_sniffed_data_brief(data)

        # Get packets from the captured data
        self.suite_logger.debug("Verify traffic is processed according to the ACLs")
        # Verify first packet is flooded
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:01:01:01'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:02:02:02'}]
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

        # Verify second packet is dropped
        params_1 = [{"layer": "Ethernet", "field": 'dst', "value": '00:00:00:03:03:03'},
                    {"layer": "Ethernet", "field": 'src', "value": '00:00:00:04:04:04'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is flooded"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[2],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is flooded"
        assert len(helpers.get_packet_from_the_port(sniff_port=sniff_ports[3],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "Packet is flooded"

    def test_acl_statistics(self, env):
        """
        @brief Simple ACL test for ACL Statistics
        @steps
            -# Configure ACL: drop all packets.
            -# Configure ACL: allow packets with Ethernet.dst=00:00:00:01:01:01.
            -# Create stream with Ethernet.dst=00:00:00:01:01:01.
            -# Create stream with Ethernet.dst=00:00:00:03:03:03.
            -# Send streams.
            -# Get ACL Statistics.
            -# Verify Statistics has been updated with correct values.
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

        # Configure ACL: drop all packets;
        # allow only packets with Ethernet.dst=00:00:00:01:01:01
        self.suite_logger.debug("Create ACLs")
        # Configure ACL Expression in format (id, expression, mask, value)
        expressions = [(1, 'SrcMac', '00:00:00:00:00:00', '00:00:00:00:00:00'),
                       (2, 'DstMac', 'FF:FF:FF:FF:FF:FF', '00:00:00:01:01:01')]

        # Configure ACL Action in format (id, action, params)
        # Additional 'Count' action should be added in order to update ACL Statistics
        actions = [(1, 'Drop', ''), (1, 'Count', ''), (2, 'Allow', ''), (2, 'Count', '')]

        # Configure ACL Rule in format
        # (id, expression_id, action_id, stage, enabled, priority)
        rules = [(1, 1, 1, 'Ingress', 'Enabled', 0), (2, 2, 2, 'Ingress', 'Enabled', 0)]

        # Create ACLs on device's ports
        try:
            env.switch[1].ui.create_acl(ports=device_ports, expressions=expressions,
                                        actions=actions, rules=rules)

        except Exception as err:
            # Exception in configuration
            self.suite_logger.debug('ACL configuration failed: %s' % err)
            pytest.fail('ACL configuration failed')

        # Wait some time for proper switch behavior
        time.sleep(1)

        # Generate test traffic
        packet_1 = ({"Ethernet": {"dst": "00:00:00:01:01:01", "src": "00:00:00:02:02:02"}},
                    {"IP": {}}, {"TCP": {}})
        packet_2 = ({"Ethernet": {"dst": "00:00:00:03:03:03", "src": "00:00:00:04:04:04"}},
                    {"IP": {}}, {"TCP": {}})
        # Send packets to the first port
        count_2 = 5
        count_1 = 10
        packet_size = 100
        stream_1 = env.tg[1].set_stream(packet_1, count=count_2,
                                        iface=sniff_ports[0], required_size=packet_size)
        stream_2 = env.tg[1].set_stream(packet_2, count=count_1,
                                        iface=sniff_ports[0], required_size=packet_size)
        streams = [stream_1, stream_2]

        self.suite_logger.debug("Start the capture and send the test traffic")
        # Start capture
        env.tg[1].start_sniff(sniff_ports, sniffing_time=10)

        #  Send generated streams
        env.tg[1].start_streams(streams)

        # Stop capture
        env.tg[1].stop_sniff(sniff_ports)

        # Stop traffic
        env.tg[1].stop_streams()

        self.suite_logger.debug("Verify ACl Statistics is updated "
                                "according to the created ACLs")
        # Get ACL Statistics
        statistics = env.switch[1].ui.get_table_acl("ACLStatistics")

        # Get statistics for first ACL Rule
        stat_1 = [x for x in statistics if x["ruleId"] == 1][0]
        # Verify statistics
        assert stat_1["matchPkts"] == count_1
        assert stat_1["matchOctets"] == count_1 * packet_size

        # Get statistics for second ACL Rule
        stat_1 = [x for x in statistics if x["ruleId"] == 2][0]
        # Verify statistics
        assert stat_1["matchPkts"] == count_2
        assert stat_1["matchOctets"] == count_2 * packet_size
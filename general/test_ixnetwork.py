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

@file test_ixnetwork.py

@summary   Samples for Traffic Generator IxNetwork configuration.

@details
Following test cases are tested:
1. IxNetwork interface and traffic configuration.
2. IxNetwork STP configuration.
3. IxNetwork LACP configuration.
4. IxNetwork OSPF configuration.
5. IxNetwork BGP configuration.
"""

import time

import pytest

from testlib import helpers


@pytest.mark.ixnet_simplified
class TestTGIxNetworkSamples(object):
    """
    @description Suite for Traffic Generator IxNetwork configuration
    """

    def test_iface_traffic_configuration(self, env):
        """
        @brief  IxNetwork interface and traffic configuration
        @note  IxNetwork HLT API has special Tcl methods in order to configure interfaces and traffic.
               TAF contains Python wrappers for these methods.
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Configure IxNetwork interface
        # Please see ::ixia::interface_config for all supported arguments
        env.tg[1].iface_config(tg_ports[0], autonegotiation='1', duplex='auto',
                               speed='auto', intf_ip_addr='10.0.0.3', gateway='10.0.0.1',
                               netmask='255.255.255.0')

        # Configure IP address and gateaway
        env.tg[1].iface_config(tg_ports[1], autonegotiation=1, duplex='auto',
                               speed='auto', intf_ip_addr='10.0.0.2', gateway='10.0.0.1',
                               netmask='255.255.255.0')

        # Configure traffic
        # Please see ::ixia::traffic_config for all supported arguments
        env.tg[1].traffic_config(
            mode='create', transmit_mode='continuous', src_dest_mesh='fully',
            route_mesh='one_to_one', circuit_type='none',
            circuit_endpoint_type='ipv4',
            emulation_src_handle="%s/%s/%s" % tuple(tg_ports[0]),
            emulation_dst_handle="%s/%s/%s" % tuple(tg_ports[1]),
            rate_percent=99, length_mode='random', frame_size_min=64, frame_size_max=1500
        )

        # Start the configured traffic
        env.tg[1].traffic_control(action='run')

        time.sleep(10)

        # Stop the configured traffic
        env.tg[1].traffic_control(action='stop')

        # Get traffic statistics
        env.tg[1].traffic_stats(tg_ports[0])
        env.tg[1].traffic_stats(tg_ports[1])

        send = int(env.tg[1].traffic_dictionary[tg_ports[0]]['stats']['aggregate']['tx']['total_pkts'])
        receive = int(env.tg[1].traffic_dictionary[tg_ports[1]]['stats']['aggregate']['rx']['total_pkts'])

        assert send <= receive

    def test_stp_emulation(self, env):
        """
        @brief  IxNetwork STP configuration.
        @note  IxNetwork HLT API has special Tcl methods in order to configure STP emulation.
               TAF contains Python wrappers for these methods.
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Configure STP bridges
        # Please see ::ixia::emulation_stp_bridge_config for all supported arguments
        env.tg[1].STP.configure_bridges(tg_ports[0],
                                        auto_pick_bridge_mac=0,
                                        auto_pick_port=1,
                                        bridge_mac='00:01:00:00:00:01',
                                        bridge_mode='mstp',
                                        bridge_priority=0,
                                        root_cost=0,
                                        count='1',
                                        root_priority=0,
                                        root_mac='00:01:00:00:00:01',
                                        forward_delay='15000',
                                        hello_interval='2000',
                                        intf_count='1',
                                        max_age='20000',
                                        message_age='0')

        # Configure STP MSTI
        # Please see ::ixia::emulation_stp_msti_config for all supported arguments
        env.tg[1].STP.configure_msti(tg_ports[0],
                                     bridge_handler_id="1",
                                     count='1',
                                     msti_id=1,
                                     msti_name='MSTI 1',
                                     msti_mac='00:01:00:00:00:01',
                                     msti_internal_root_path_cost=0,
                                     msti_priority=0,
                                     msti_vlan_start=10,
                                     msti_vlan_stop=11)

        # Start STP in IxNetwork
        env.tg[1].STP.control(tg_ports[0], bridge_handler_id='1', mode="start")

    def test_lacp_emulation(self, env):
        """
        @brief  IxNetwork LACP configuration.
        @note  IxNetwork HLT API has special Tcl methods in order to configure LACP emulation.
               TAF contains Python wrappers for these methods.
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = tuple(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Configure TG interfaces
        for tgport in tg_ports:
            env.tg[1].iface_config(tgport, autonegotiation='1', duplex='auto')

        # Configure LACP on TG interfaces
        # Please see ::ixia::emulation_lacp_link_config for all supported arguments
        lacplinks = env.tg[1].LACP.configure_links(tg_ports, mode='create',
                                                   reset=True, lag_count='1',
                                                   port_handle='$port_handle',
                                                   actor_key='0',
                                                   actor_port_num='2',
                                                   actor_port_num_step='1',
                                                   actor_port_pri='4096',
                                                   actor_system_id='0000.1111.0000',
                                                   actor_system_pri='8192',
                                                   auto_pick_port_mac='1',
                                                   collector_max_delay='10',
                                                   lacp_activity='active',
                                                   lacp_timeout='short',
                                                   lacpdu_periodic_time_interval='auto')
        for lacp_link in lacplinks:
            env.tg[1].LACP.configure_links(tg_ports,
                                           link_handler_id=lacp_link,
                                           mode='enable')

        # Start LACP
        env.tg[1].LACP.control(tg_ports, mode='start')

    def test_ospf_emulation(self, env):
        """
        @brief  IxNetwork OSPF configuration.
        @note  IxNetwork HLT API has special Tcl methods in order to configure OSPF emulation.
               TAF contains Python wrappers for these methods.
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        tgport1 = ports[('tg1', 'sw1')][1]

        # Configure OSPF
        # Please see ::ixia::emulation_ospf_config for all supported arguments
        session_handle_1 = env.tg[1].OSPF.config(
            tgport1,
            reset=True,
            mode='create',
            mac_address_init='0000.0a01.0002',
            intf_ip_addr='10.1.0.2',
            router_id='2.2.2.2',
            area_id='0.0.0.0',
            router_priority=1,
            neighbor_intf_ip_addr='10.1.0.1',
            lsa_discard_mode=0,
            enable_dr_bdr=1,
            mtu=1500,
            session_type='ospfv2')

        # Configure OSPF routes
        # Please see ::ixia::emulation_ospf_topology_route_config for all supported arguments
        env.tg[1].OSPF.topology_route_config(
            session_handle_1,
            summary_number_of_prefix=1,
            summary_prefix_start='10.2.0.1',
            summary_prefix_length=24,
            summary_prefix_metric=20,
            summary_route_type='same_area',
            type='summary_routes')

        # start OSPF
        env.tg[1].OSPF.ospf_control(session_handle_1, mode='start')

    def test_bgp_emulation(self, env):
        """
        @brief  IxNetwork BGP configuration.
        @note  IxNetwork HLT API has special Tcl methods in order to configure DGP emulation.
               TAF contains Python wrappers for these methods.
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        # Configure BGP
        # Please see ::ixia::emulation_bgp_config for all supported arguments
        env.tg[1].BGP.configure_neighbour(tg_ports[0],
                                          mode='enable',
                                          local_ip_addr='20.20.20.2',
                                          remote_ip_addr='20.20.20.1',
                                          count='1',
                                          hold_time=5,
                                          neighbor_type='internal',
                                          ip_version='4',
                                          vlan_id=1,
                                          local_as=7675,
                                          local_router_id='1.1.1.2')

        # Start BGP
        env.tg[1].BGP.control(port=tg_ports[0], mode='start')
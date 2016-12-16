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

@file test_tg.py

@summary   Samples for Traffic Generator configuration.

@details
Following test cases are tested:
1. Create simple streams, streams configuration.
2. Capture configuration.
3. Work with Statistics.
4. IxNetwork protocols.
"""

import time

import pytest

from testlib import helpers


@pytest.mark.simplified
class TestTGSamples(object):
    """
    @description Suite for Traffic Generator configuration
    """

    def test_stream_configuration(self, env):
        """
        @brief  Create simple streams, streams configuration
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Create simple stream")
        # Create packet definition in format
        # list[dict{LAYER_NAME: dict{LAYER_ATTR: VAL}}]
        packet_definition = [{'Ethernet': {'src': '00:00:11:11:11:11',
                                        'dst': '00:00:22:22:22:22'}},
                             {'IP': {'src': '11.11.0.12',
                                     'dst': '12.12.0.15'}}
                             ]

        # 1. Configure stream: send 5 packets from link 1
        stream_1 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0], count=5)

        # Send configured stream
        env.tg[1].send_stream(stream_1)

        # 2. Change packet size
        stream_2 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        count=5, required_size=120)

        # Send two stream simultaneously
        env.tg[1].start_streams([stream_1, stream_2])
        time.sleep(2)

        # Stop streams
        env.tg[1].stop_streams([stream_1, stream_2])

        # 3. Configure continuous traffic
        stream_3 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        continuous=True)

        # 4. Configure traffic rate in percent from maximum
        # Note: rate is supported only on Ixia
        stream_4 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        continuous=True, rate=50)

        # 5. Configure interval between frames in seconds
        stream_5 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        continuous=True, inter=1)

        # 6. Configure stream with error: set force_errors to none|bad|dribble|align
        # Note: force_errors is supported only on Ixia
        stream_6 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        count=1, force_errors='bad')

        # 7. Configure increments
        # for more details see testlib/tg_template.set_stream

        # Ethernet.src increment: step 2, count 20
        stream_7 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        sa_increment=(2, 20), count=20)

        # IP.src continuous increment with step 2
        stream_8 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        sip_increment=(2, 0), continuous=True)

        # Frame size increment: initial size 70, step 2, max size 78
        stream_9 = env.tg[1].set_stream(packet_definition, iface=tg_ports[0],
                                        count=10, required_size=('Increment', 2, 70, 78))

        # Start all configured streams
        streams = [stream_1, stream_2, stream_3, stream_4, stream_5,
                   stream_6, stream_7, stream_8, stream_9]
        env.tg[1].start_streams(streams)
        time.sleep(5)
        # Stop first four streams
        env.tg[1].stop_streams([stream_1, stream_2, stream_3, stream_4])
        time.sleep(5)
        # Stop all streams
        env.tg[1].stop_streams()

    def test_capture(self, env):
        """
        @brief  Capture configuration
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Create simple streams")
        # Create packet definition in format
        # list[dict{LAYER_NAME: dict{LAYER_ATTR: VAL}}]
        packet_definition_1 = [{'Ethernet': {'src': '00:00:00:11:11:11',
                                             'dst': '00:00:00:22:22:22'}},
                               {'IP': {}}
                               ]

        packet_definition_2 = [{'Ethernet': {'src': '00:00:00:33:33:33',
                                             'dst': '00:00:00:44:44:44'}},
                               {'IP': {'src': '192.168.0.12',
                                       'dst': '192.168.0.15'}}
                               ]

        # Configure stream: send 5 packets from link 1
        stream_1 = env.tg[1].set_stream(packet_definition_1, iface=tg_ports[0], count=5)
        stream_2 = env.tg[1].set_stream(packet_definition_2, iface=tg_ports[0], count=5)

        # 1. Start capture on TG ports for 5 seconds
        env.tg[1].start_sniff(tg_ports, sniffing_time=5)

        # Send stream
        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        # TAF will wait 'sniffing_time' to stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames in DEBUG mode
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 2. Configure filter by layer: please see list of available
        # layers in testlib.packet_processor.flt_patterns .
        # Capture IP frames
        env.tg[1].start_sniff(tg_ports, sniffing_time=5, filter_layer='IP')

        # Send stream
        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "non IP packets were received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 3. Configure filter by Ethernet.src
        env.tg[1].start_sniff(tg_ports, sniffing_time=5, src_filter='00:00:00:33:33:33')

        # Send stream
        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "non IP packets were received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 4. Configure filter by Ethernet.dst
        env.tg[1].start_sniff(tg_ports, sniffing_time=5, dst_filter='00:00:00:44:44:44')

        # Send stream
        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "non IP packets were received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 5. User can combine filter_layer with src and dst filters
        # Configure filter by Ethernet.dst and IP layer
        env.tg[1].start_sniff(tg_ports, sniffing_time=5, dst_filter='00:00:00:44:44:44',
                              filter_layer='IP')

        # Send stream
        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "non IP packets were received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 6. Capture certain number of frames
        # However filtering works after packets were received,
        # so real number of frames could be less than expected
        env.tg[1].env.tg[1].start_sniff([tg_ports[1], tg_ports[2]], packets_count=3,
                                        filter_layer='IP')

        env.tg[1].start_streams([stream_1, stream_2])

        # Stop capture
        data = env.tg[1].stop_sniff([tg_ports[1], tg_ports[2]])

        # Print captured frames
        helpers.print_sniffed_data_brief(data)

        env.tg[1].stop_streams([stream_1, stream_2])

        # Verify received frames
        params_1 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:11:11:11'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:22:22:22'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_1,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 0, \
            "non IP packets were received"

        params_2 = [{"layer": "Ethernet", "field": 'src', "value": '00:00:00:33:33:33'},
                    {"layer": "Ethernet", "field": 'dst', "value": '00:00:00:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params_2,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) <= 3, \
            "Packets are not received"

        # 7. Stop capture immediately
        env.tg[1].start_sniff(tg_ports, sniffing_time=30)
        time.sleep(5)
        env.tg[1].stop_sniff(tg_ports, force=True)

        # 8. Change captured buffer size (1000 frames by default)
        env.tg[1].start_sniff(tg_ports, sniffing_time=3)
        # TAF will return only 5 frames from buffer for each port
        env.tg[1].stop_sniff(tg_ports, sniff_packet_count=5)

        # 9. Ignore frames in the captured buffer
        # use in case test doesn't process captured frames, but
        # makes decisions based on statistics values
        env.tg[1].start_sniff(tg_ports, sniffing_time=3)
        # TAF will return only 5 frames from buffer for each port
        env.tg[1].stop_sniff(tg_ports, drop_packets=True)

    def test_statistics(self, env):
        """
        @brief  Work with Statistics
        """
        # Get available TG ports from the environment
        ports = env.get_ports([['tg1', 'sw1', 4], ])
        tg_ports = list(ports[('tg1', 'sw1')].values())
        # Set necessary ports in Up state
        helpers.set_ports_admin_enabled(env.switch, ports)

        self.suite_logger.debug("Create simple streams")
        # Create packet definition in format
        # list[dict{LAYER_NAME: dict{LAYER_ATTR: VAL}}]
        packet_definition = [{'Ethernet': {'src': '00:00:33:33:33:33',
                                           'dst': '00:00:44:44:44:44'}},
                             {'IP': {'src': '20.20.0.12',
                                     'dst': '20.20.0.15'}}
                             ]

        # Configure stream: send 5 packets from link 1
        stream = env.tg[1].set_stream(packet_definition, iface=tg_ports[0], count=5)

        # 1. Clear Ports statistics
        env.tg[1].clear_statistics(tg_ports)

        # Start capture on TG ports for 5 seconds
        env.tg[1].start_sniff(tg_ports, sniffing_time=5, filter_layer='IP')

        # Send stream
        env.tg[1].send_stream(stream)

        # Stop capture
        data = env.tg[1].stop_sniff(tg_ports)

        # Print captured frames in DEBUG mode
        helpers.print_sniffed_data_brief(data)

        # Verify received frames
        params = [{"layer": "Ethernet", "field": 'src', "value": '00:00:33:33:33:33'},
                  {"layer": "Ethernet", "field": 'dst', "value": '00:00:44:44:44:44'}]
        assert len(helpers.get_packet_from_the_port(sniff_port=tg_ports[1],
                                                    params=params,
                                                    sniff_data=data,
                                                    tg=env.tg[1])) == 5, \
            "Packets are not received"

        # 2. Get sent statistics
        sent_cont = env.tg[1].get_sent_frames_count(tg_ports[0])
        assert sent_cont == 5

        # 3. Get received frames count (filtered + unfiltered)
        received_count = env.tg[1].get_received_frames_count(tg_ports[1])
        assert received_count >= 5

        # 4. Get filtered frames count
        filtered_count = env.tg[1].get_filtered_frames_count(tg_ports[1])
        assert filtered_count == 5

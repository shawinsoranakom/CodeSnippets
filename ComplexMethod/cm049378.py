def on_message(self, ws, messages):
        """Synchronously handle messages received by the websocket."""
        for message in json.loads(messages):
            self.last_message_id = message['id']
            payload = message['message']['payload']
            _logger.info("Received message of type %s", message['message']['type'])

            if not helpers.get_identifier() in payload.get('iot_identifiers', []):
                continue

            match message['message']['type']:
                case 'iot_action':
                    for device_identifier in payload['device_identifiers']:
                        if device_identifier in main.iot_devices:
                            start_operation_time = time.perf_counter()
                            _logger.info("device '%s' action started", device_identifier)
                            main.iot_devices[device_identifier].action(payload)
                            _logger.info("device '%s' action finished - %.*f", device_identifier, 3, time.perf_counter() - start_operation_time)
                        else:
                            # Notify the controller that the device is not connected
                            send_to_controller({
                                'session_id': payload.get('session_id', '0'),
                                'iot_box_identifier': helpers.get_identifier(),
                                'device_identifier': device_identifier,
                                'status': 'disconnected',
                            })
                case 'server_clear':
                    if time.monotonic() < self.connect_timestamp + 5.0:
                        # This is a hacky way avoid processing an old server_clear message
                        # In master we can fix this properly by providing the last message ID to the IoT box on connection
                        _logger.warning("Ignoring server_clear message")
                        continue
                    helpers.disconnect_from_server()
                    close_server_log_sender_handler()
                case 'server_update':
                    helpers.update_conf({
                        'remote_server': payload['server_url']
                    })
                    helpers.get_odoo_server_url.cache_clear()
                case 'restart_odoo':
                    send_to_controller({
                        'session_id': payload['session_id'],
                        'iot_box_identifier': helpers.get_identifier(),
                        'device_identifier': helpers.get_identifier(),
                        'status': 'success',
                    })
                    ws.close()
                    helpers.odoo_restart()
                case 'webrtc_offer':
                    if not webrtc_client:
                        continue
                    answer = webrtc_client.offer(payload['offer'])
                    send_to_controller({
                        'iot_box_identifier': helpers.get_identifier(),
                        'answer': answer,
                    }, method="webrtc_answer")
                case 'remote_debug':
                    if platform.system() == 'Windows':
                        continue
                    if not payload.get("status"):
                        helpers.toggle_remote_connection(payload.get("token", ""))
                        time.sleep(1)
                    send_to_controller({
                        'session_id': 0,
                        'iot_box_identifier': helpers.get_identifier(),
                        'device_identifier': None,
                        'status': 'success',
                        'result': {'enabled': helpers.is_ngrok_enabled()}
                    })
                case "test_connection":
                    send_to_controller({
                        'session_id': payload['session_id'],
                        'iot_box_identifier': helpers.get_identifier(),
                        'device_identifier': helpers.get_identifier(),
                        'status': 'success',
                        'result': {
                            'lan_quality': helpers.check_network(),
                            'wan_quality': helpers.check_network("www.odoo.com"),
                        }
                    })
                case 'bundle_changed':
                    # This message is sent by the DB whenever the web JS asset bundle changes.
                    # While this is a bit of a hack we use this message to check if the DB has been upgraded,
                    # since we know the bundle will always change in this situation.
                    upgrade.check_git_branch()
                case _:
                    continue
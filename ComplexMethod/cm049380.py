async def on_message(message_str: str):
                # Handle chunked message
                if self.chunked_message_in_progress.get(channel) is not None:
                    if message_str == "chunked_end":
                        message_str = self.chunked_message_in_progress.pop(channel)
                    else:
                        self.chunked_message_in_progress[channel] += message_str
                        return
                elif message_str == "chunked_start":
                    self.chunked_message_in_progress[channel] = ""
                    return

                # Handle regular message
                message = json.loads(message_str)
                message_type = message["message_type"]
                _logger.info("Received message of type %s", message_type)
                if message_type == "iot_action":
                    device_identifier = message["device_identifier"]
                    data = message["data"]
                    data["session_id"] = message["session_id"]
                    if device_identifier in main.iot_devices:
                        start_operation_time = time.perf_counter()
                        _logger.info("device '%s' action started", device_identifier)
                        await self.event_loop.run_in_executor(None, lambda: main.iot_devices[device_identifier].action(data))
                        _logger.info("device '%s' action finished - %.*f", device_identifier, 3, time.perf_counter() - start_operation_time)
                    else:
                        # Notify that the device is not connected
                        self.send({
                            'owner': message['session_id'],
                            'device_identifier': device_identifier,
                            'time': time.time(),
                            'status': 'disconnected',
                        })
                elif message_type == "test_protocol":
                    self.send({
                        'owner': message['session_id'],
                        'device_identifier': helpers.get_identifier(),
                        'time': time.time(),
                        'status': 'success',
                    })
                elif message_type == "restart_odoo":
                    self.send({
                        'owner': message['session_id'],
                        'device_identifier': helpers.get_identifier(),
                        'time': time.time(),
                        'status': 'success',
                    })
                    await self.event_loop.run_in_executor(None, helpers.odoo_restart)
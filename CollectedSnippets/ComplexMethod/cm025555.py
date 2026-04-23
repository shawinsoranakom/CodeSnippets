async def _event_listener(self) -> None:
        """Match event with listener for event type."""
        retry_time = 10
        while True:
            try:
                async for event_message in self.client.stream_all_events():
                    retry_time = 10
                    event_message_ha_id = event_message.ha_id
                    if event_message_ha_id in self.appliance_coordinators:
                        if event_message.type == EventType.DEPAIRED:
                            appliance_coordinator = self.appliance_coordinators.pop(
                                event_message.ha_id
                            )
                            await appliance_coordinator.async_shutdown()
                        else:
                            appliance_coordinator = self.appliance_coordinators[
                                event_message.ha_id
                            ]
                            if not appliance_coordinator.data.info.connected:
                                appliance_coordinator.data.info.connected = True
                                appliance_coordinator.call_all_event_listeners()

                    elif event_message.type == EventType.PAIRED:
                        appliance_coordinator = HomeConnectApplianceCoordinator(
                            self.hass,
                            self.config_entry,
                            self.client,
                            self.global_listeners,
                            await self.client.get_specific_appliance(
                                event_message_ha_id
                            ),
                        )
                        await appliance_coordinator.async_register_shutdown()
                        self.appliance_coordinators[event_message.ha_id] = (
                            appliance_coordinator
                        )

                    assert appliance_coordinator
                    await appliance_coordinator.event_listener(event_message)

            except (EventStreamInterruptedError, HomeConnectRequestError) as error:
                _LOGGER.debug(
                    "Non-breaking error (%s) while listening for events,"
                    " continuing in %s seconds",
                    error,
                    retry_time,
                )
                await asyncio_sleep(retry_time)
                retry_time = min(retry_time * 2, 3600)
            except HomeConnectApiError as error:
                _LOGGER.error("Error while listening for events: %s", error)
                self.hass.config_entries.async_schedule_reload(
                    self.config_entry.entry_id
                )
                break
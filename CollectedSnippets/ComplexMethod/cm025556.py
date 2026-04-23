async def event_listener(self, event_message: EventMessage) -> None:
        """Match event with listener for event type."""

        match event_message.type:
            case EventType.STATUS:
                statuses = self.data.status
                for event in event_message.data.items:
                    status_key = StatusKey(event.key)
                    if status_key in statuses:
                        statuses[status_key].value = event.value
                    else:
                        statuses[status_key] = Status(
                            key=status_key,
                            raw_key=status_key.value,
                            value=event.value,
                        )
                    if (
                        status_key == StatusKey.BSH_COMMON_OPERATION_STATE
                        and event.value == BSH_OPERATION_STATE_PAUSE
                        and CommandKey.BSH_COMMON_RESUME_PROGRAM
                        not in (commands := self.data.commands)
                    ):
                        # All the appliances that can be paused
                        # should have the resume command available.
                        commands.add(CommandKey.BSH_COMMON_RESUME_PROGRAM)
                        for (
                            listener,
                            context,
                        ) in self.global_listeners.values():
                            if EventKey.BSH_COMMON_APPLIANCE_DEPAIRED not in context:
                                listener()
                self._call_event_listener(event_message)

            case EventType.NOTIFY:
                settings = self.data.settings
                events = self.data.events
                program_update_event_value = None
                for event in event_message.data.items:
                    event_key = event.key
                    if event_key in SettingKey.__members__.values():  # type: ignore[comparison-overlap]
                        setting_key = SettingKey(event_key)
                        if setting_key in settings:
                            settings[setting_key].value = event.value
                        else:
                            settings[setting_key] = GetSetting(
                                key=setting_key,
                                raw_key=setting_key.value,
                                value=event.value,
                            )
                    else:
                        event_value = event.value
                        if event_key in (
                            EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM,
                            EventKey.BSH_COMMON_ROOT_SELECTED_PROGRAM,
                        ) and isinstance(event_value, str):
                            program_update_event_value = ProgramKey(event_value)
                        events[event_key] = event
                # Process program update after all events to ensure
                # BSH_COMMON_OPTION_BASE_PROGRAM event is available for
                # favorite program resolution
                if program_update_event_value:
                    await self.update_options(program_update_event_value)
                self._call_event_listener(event_message)

            case EventType.EVENT:
                events = self.data.events
                for event in event_message.data.items:
                    events[event.key] = event
                self._call_event_listener(event_message)

            case EventType.CONNECTED | EventType.PAIRED:
                if self.refreshed_too_often_recently():
                    return

                await self.async_refresh()
                for (
                    listener,
                    context,
                ) in self.global_listeners.values():
                    if EventKey.BSH_COMMON_APPLIANCE_DEPAIRED not in context:
                        listener()
                self.call_all_event_listeners()

            case EventType.DISCONNECTED:
                self.data.info.connected = False
                self.call_all_event_listeners()

            case EventType.DEPAIRED:
                device = self.device_registry.async_get_device(
                    identifiers={(DOMAIN, self.data.info.ha_id)}
                )
                if device:
                    self.device_registry.async_update_device(
                        device_id=device.id,
                        remove_config_entry_id=self._config_entry.entry_id,
                    )
                for (
                    listener,
                    context,
                ) in self.global_listeners.values():
                    assert isinstance(context, tuple)
                    if EventKey.BSH_COMMON_APPLIANCE_DEPAIRED in context:
                        listener()
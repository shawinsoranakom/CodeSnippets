async def update_options(self, program_key: ProgramKey) -> None:
        """Update options for appliance."""
        options = self.data.options
        events = self.data.events
        options_to_notify = options.copy()
        options.clear()
        if (
            program_key
            in (
                ProgramKey.BSH_COMMON_FAVORITE_001,
                ProgramKey.BSH_COMMON_FAVORITE_002,
            )
            and (event := events.get(EventKey.BSH_COMMON_OPTION_BASE_PROGRAM))
            and isinstance(event.value, str)
        ):
            # The API doesn't allow to fetch the options from the favorite program.
            # We can attempt to get the base program and get the options
            resolved_program_key = ProgramKey(event.value)
        else:
            resolved_program_key = program_key

        options.update(await self.get_options_definitions(resolved_program_key))

        for option in options.values():
            option_value = option.constraints.default if option.constraints else None
            if option_value is not None:
                option_event_key = EventKey(option.key)
                events[option_event_key] = Event(
                    option_event_key,
                    option.key.value,
                    0,
                    "",
                    "",
                    option_value,
                    option.name,
                    unit=option.unit,
                )
        options_to_notify.update(options)
        for option_key in options_to_notify:
            for listener in self._get_listeners_for_event_key(EventKey(option_key)):
                listener()
async def get_appliance_data(self) -> None:
        """Get appliance data."""
        appliance = self.data.info
        self.device_registry.async_get_or_create(
            config_entry_id=self._config_entry.entry_id,
            identifiers={(DOMAIN, appliance.ha_id)},
            manufacturer=appliance.brand,
            name=appliance.name,
            model=appliance.vib,
        )
        if not appliance.connected:
            self.data.update(HomeConnectApplianceData.empty(appliance))
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="appliance_disconnected",
                translation_placeholders={
                    "appliance_name": appliance.name,
                    "ha_id": appliance.ha_id,
                },
            )
        try:
            settings = {
                setting.key: setting
                for setting in (
                    await self.client.get_settings(appliance.ha_id)
                ).settings
            }
        except TooManyRequestsError:
            raise
        except HomeConnectError as error:
            _LOGGER.debug(
                "Error fetching settings for %s: %s",
                appliance.ha_id,
                error,
            )
            settings = {}
        try:
            status = {
                status.key: status
                for status in (await self.client.get_status(appliance.ha_id)).status
            }
        except TooManyRequestsError:
            raise
        except HomeConnectError as error:
            _LOGGER.debug(
                "Error fetching status for %s: %s",
                appliance.ha_id,
                error,
            )
            status = {}

        programs = []
        events = {}
        options = {}
        if appliance.type in APPLIANCES_WITH_PROGRAMS:  # pylint: disable=too-many-nested-blocks
            try:
                all_programs = await self.client.get_all_programs(appliance.ha_id)
            except TooManyRequestsError:
                raise
            except HomeConnectError as error:
                _LOGGER.debug(
                    "Error fetching programs for %s: %s",
                    appliance.ha_id,
                    error,
                )
            else:
                programs.extend(all_programs.programs)
                current_program_key = None
                program_options = None
                for program, event_key in (
                    (
                        all_programs.selected,
                        EventKey.BSH_COMMON_ROOT_SELECTED_PROGRAM,
                    ),
                    (
                        all_programs.active,
                        EventKey.BSH_COMMON_ROOT_ACTIVE_PROGRAM,
                    ),
                ):
                    if program and program.key:
                        events[event_key] = Event(
                            event_key,
                            event_key.value,
                            0,
                            "",
                            "",
                            program.key,
                        )
                        current_program_key = program.key
                        program_options = program.options
                        if (
                            current_program_key
                            in (
                                ProgramKey.BSH_COMMON_FAVORITE_001,
                                ProgramKey.BSH_COMMON_FAVORITE_002,
                            )
                            and program_options
                        ):
                            # The API doesn't allow to fetch the options from the favorite program.
                            # We can attempt to get the base program and get the options
                            for option in program_options:
                                if option.key == OptionKey.BSH_COMMON_BASE_PROGRAM:
                                    current_program_key = ProgramKey(option.value)
                                    break

                if current_program_key:
                    options = await self.get_options_definitions(current_program_key)
                    for option in program_options or []:
                        option_event_key = EventKey(option.key)
                        events[option_event_key] = Event(
                            option_event_key,
                            option.key,
                            0,
                            "",
                            "",
                            option.value,
                            option.name,
                            display_value=option.display_value,
                            unit=option.unit,
                        )

        try:
            commands = {
                command.key
                for command in (
                    await self.client.get_available_commands(appliance.ha_id)
                ).commands
            }
        except TooManyRequestsError:
            raise
        except HomeConnectError:
            commands = set()

        self.data.update(
            HomeConnectApplianceData(
                commands=commands,
                events=events,
                info=appliance,
                options=options,
                programs=programs,
                settings=settings,
                status=status,
            )
        )
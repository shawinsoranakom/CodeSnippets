async def async_step_configure_receiver(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the configuration of a single receiver."""
        errors = {}

        reconfigure_entry = None
        schema = STEP_CONFIGURE_SCHEMA
        if self.source == SOURCE_RECONFIGURE:
            schema = STEP_RECONFIGURE_SCHEMA
            reconfigure_entry = self._get_reconfigure_entry()

        if user_input is not None:
            volume_resolution = user_input[OPTION_VOLUME_RESOLUTION]

            if reconfigure_entry is not None:
                entry_options = reconfigure_entry.options
                result = self.async_update_reload_and_abort(
                    reconfigure_entry,
                    data={
                        CONF_HOST: self._receiver_info.host,
                    },
                    options={
                        **entry_options,
                        OPTION_VOLUME_RESOLUTION: volume_resolution,
                    },
                )

                _LOGGER.debug("Reconfigured receiver, result: %s", result)
                return result

            input_source_meanings: list[str] = user_input[OPTION_INPUT_SOURCES]
            if not input_source_meanings:
                errors[OPTION_INPUT_SOURCES] = "empty_input_source_list"

            listening_modes: list[str] = user_input[OPTION_LISTENING_MODES]
            if not listening_modes:
                errors[OPTION_LISTENING_MODES] = "empty_listening_mode_list"

            if not errors:
                input_sources_store: dict[str, str] = {}
                for input_source_meaning in input_source_meanings:
                    input_source = INPUT_SOURCES_ALL_MEANINGS[input_source_meaning]
                    input_sources_store[input_source.value] = input_source_meaning

                listening_modes_store: dict[str, str] = {}
                for listening_mode_meaning in listening_modes:
                    listening_mode = LISTENING_MODES_ALL_MEANINGS[
                        listening_mode_meaning
                    ]
                    listening_modes_store[listening_mode.value] = listening_mode_meaning

                result = self.async_create_entry(
                    title=self._receiver_info.model_name,
                    data={
                        CONF_HOST: self._receiver_info.host,
                    },
                    options={
                        OPTION_VOLUME_RESOLUTION: volume_resolution,
                        OPTION_MAX_VOLUME: OPTION_MAX_VOLUME_DEFAULT,
                        OPTION_INPUT_SOURCES: input_sources_store,
                        OPTION_LISTENING_MODES: listening_modes_store,
                    },
                )

                _LOGGER.debug("Configured receiver, result: %s", result)
                return result

        _LOGGER.debug("Configuring receiver, info: %s", self._receiver_info)

        suggested_values = user_input
        if suggested_values is None:
            if reconfigure_entry is None:
                suggested_values = {
                    OPTION_VOLUME_RESOLUTION: OPTION_VOLUME_RESOLUTION_DEFAULT,
                    OPTION_INPUT_SOURCES: [
                        get_meaning(input_source)
                        for input_source in INPUT_SOURCES_DEFAULT
                    ],
                    OPTION_LISTENING_MODES: [
                        get_meaning(listening_mode)
                        for listening_mode in LISTENING_MODES_DEFAULT
                    ],
                }
            else:
                entry_options = reconfigure_entry.options
                suggested_values = {
                    OPTION_VOLUME_RESOLUTION: entry_options[OPTION_VOLUME_RESOLUTION],
                }

        return self.async_show_form(
            step_id="configure_receiver",
            data_schema=self.add_suggested_values_to_schema(schema, suggested_values),
            errors=errors,
            description_placeholders={
                "name": f"{self._receiver_info.model_name} ({self._receiver_info.host})"
            },
        )
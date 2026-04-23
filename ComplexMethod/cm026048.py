async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors = {}

        entry_options: Mapping[str, Any] = self.config_entry.options
        entry_options = {
            OPTION_LISTENING_MODES: {
                listening_mode.value: get_meaning(listening_mode)
                for listening_mode in LISTENING_MODES_DEFAULT
            },
            **entry_options,
        }

        if user_input is not None:
            input_source_meanings: list[str] = user_input[OPTION_INPUT_SOURCES]
            if not input_source_meanings:
                errors[OPTION_INPUT_SOURCES] = "empty_input_source_list"

            listening_mode_meanings: list[str] = user_input[OPTION_LISTENING_MODES]
            if not listening_mode_meanings:
                errors[OPTION_LISTENING_MODES] = "empty_listening_mode_list"

            if not errors:
                self._input_sources = {}
                for input_source_meaning in input_source_meanings:
                    input_source = INPUT_SOURCES_ALL_MEANINGS[input_source_meaning]
                    input_source_name = entry_options[OPTION_INPUT_SOURCES].get(
                        input_source.value, input_source_meaning
                    )
                    self._input_sources[input_source] = input_source_name

                self._listening_modes = {}
                for listening_mode_meaning in listening_mode_meanings:
                    listening_mode = LISTENING_MODES_ALL_MEANINGS[
                        listening_mode_meaning
                    ]
                    listening_mode_name = entry_options[OPTION_LISTENING_MODES].get(
                        listening_mode.value, listening_mode_meaning
                    )
                    self._listening_modes[listening_mode] = listening_mode_name

                self._data = {
                    OPTION_VOLUME_RESOLUTION: entry_options[OPTION_VOLUME_RESOLUTION],
                    OPTION_MAX_VOLUME: user_input[OPTION_MAX_VOLUME],
                }

                return await self.async_step_names()

        suggested_values = user_input
        if suggested_values is None:
            suggested_values = {
                OPTION_MAX_VOLUME: entry_options[OPTION_MAX_VOLUME],
                OPTION_INPUT_SOURCES: [
                    get_meaning(InputSource(input_source))
                    for input_source in entry_options[OPTION_INPUT_SOURCES]
                ],
                OPTION_LISTENING_MODES: [
                    get_meaning(ListeningMode(listening_mode))
                    for listening_mode in entry_options[OPTION_LISTENING_MODES]
                ],
            }

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_STEP_INIT_SCHEMA, suggested_values
            ),
            errors=errors,
        )
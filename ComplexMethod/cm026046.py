async def async_step_manual(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual device entry."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            _LOGGER.debug("Config flow manual: %s", host)
            try:
                info = await async_interview(host)
            except TimeoutError:
                _LOGGER.warning("Timed out interviewing: %s", host)
                errors["base"] = "cannot_connect"
            except OSError:
                _LOGGER.exception("Unexpected exception interviewing: %s", host)
                errors["base"] = "unknown"
            else:
                self._receiver_info = info

                await self.async_set_unique_id(info.identifier, raise_on_progress=False)
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                else:
                    self._abort_if_unique_id_configured()

                return await self.async_step_configure_receiver()

        suggested_values = user_input
        if suggested_values is None and self.source == SOURCE_RECONFIGURE:
            suggested_values = {
                CONF_HOST: self._get_reconfigure_entry().data[CONF_HOST]
            }

        return self.async_show_form(
            step_id="manual",
            data_schema=self.add_suggested_values_to_schema(
                STEP_MANUAL_SCHEMA, suggested_values
            ),
            errors=errors,
        )
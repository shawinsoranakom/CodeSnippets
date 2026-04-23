async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self.host = user_input[CONF_HOST]
            if self.source == SOURCE_USER:
                self._async_abort_entries_match({CONF_HOST: user_input[CONF_HOST]})
            try:
                # Use load_selector = 0 to fetch the panel model without authentication.
                (model, _) = await try_connect(user_input, 0)
            except (
                OSError,
                ConnectionRefusedError,
                ssl.SSLError,
                asyncio.exceptions.TimeoutError,
            ) as e:
                _LOGGER.error("Connection Error: %s", e)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                self._data = user_input
                self._data[CONF_MODEL] = model

                if self.source == SOURCE_RECONFIGURE:
                    if (
                        self._get_reconfigure_entry().data[CONF_MODEL]
                        != self._data[CONF_MODEL]
                    ):
                        return self.async_abort(reason="device_mismatch")
                return await self.async_step_auth()
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )
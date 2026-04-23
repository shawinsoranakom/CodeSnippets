async def async_step_device_config(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle device configuration step.

        We ask for the PIN in this step.
        """

        if user_input is None:
            return self.async_show_form(
                step_id="device_config", data_schema=STEP_DEVICE_CONFIG_DATA_SCHEMA
            )

        errors = {}

        try:
            afsapi = AFSAPI(self._webfsapi_url, user_input[CONF_PIN])

            self._name = await afsapi.get_friendly_name()

        except FSConnectionError:
            errors["base"] = "cannot_connect"
        except InvalidPinError:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            if self.source == SOURCE_REAUTH:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_PIN: user_input[CONF_PIN]},
                )

            try:
                unique_id = await afsapi.get_radio_id()
            except FSNotImplementedError:
                unique_id = None
            await self.async_set_unique_id(unique_id, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return await self._async_create_entry(user_input[CONF_PIN])

        data_schema = self.add_suggested_values_to_schema(
            STEP_DEVICE_CONFIG_DATA_SCHEMA, user_input
        )
        return self.async_show_form(
            step_id="device_config",
            data_schema=data_schema,
            errors=errors,
        )
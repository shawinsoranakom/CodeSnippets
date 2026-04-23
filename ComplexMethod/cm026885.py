async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            client = WaterFurnace(username, password)

            try:
                # Login is a blocking call, run in executor
                await self.hass.async_add_executor_job(client.login)
            except WFCredentialError:
                errors["base"] = "invalid_auth"
            except WFException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error connecting to WaterFurnace")
                errors["base"] = "unknown"

            if not errors and not client.devices:
                errors["base"] = "no_devices"

            if not errors and client.account_id is None:
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(str(client.account_id))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"WaterFurnace {username}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
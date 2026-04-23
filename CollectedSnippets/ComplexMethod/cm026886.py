async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        errors: dict[str, str] = {}

        reauth_entry = self._get_reauth_entry()
        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            client = WaterFurnace(username, password)

            try:
                await self.hass.async_add_executor_job(client.login)
            except WFCredentialError:
                errors["base"] = "invalid_auth"
            except WFException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected error during reauthentication")
                errors["base"] = "unknown"

            if not errors and client.account_id is None:
                errors["base"] = "cannot_connect"

            if not errors:
                await self.async_set_unique_id(str(client.account_id))
                self._abort_if_unique_id_mismatch(reason="wrong_account")

                return self.async_update_reload_and_abort(
                    reauth_entry,
                    title=f"WaterFurnace {username}",
                    data_updates={**reauth_entry.data, **user_input},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA,
                {CONF_USERNAME: reauth_entry.data[CONF_USERNAME]},
            ),
            errors=errors,
        )
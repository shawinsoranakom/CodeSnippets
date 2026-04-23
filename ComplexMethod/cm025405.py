async def async_step_code(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}
        assert self._client
        assert self._username
        if user_input is not None:
            code = user_input[CONF_ENTRY_CODE]
            _LOGGER.debug("Logging into Roborock account using email provided code")
            try:
                user_data = await self._client.code_login_v4(code)
            except RoborockInvalidCode:
                errors["base"] = "invalid_code"
            except RoborockAccountDoesNotExist:
                errors["base"] = "invalid_email_or_region"
            except RoborockException:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown_roborock"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(user_data.rruid)
                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch(reason="wrong_account")
                    reauth_entry = self._get_reauth_entry()
                    return self.async_update_reload_and_abort(
                        reauth_entry, data_updates={CONF_USER_DATA: user_data.as_dict()}
                    )
                self._abort_if_unique_id_configured(error="already_configured_account")
                return await self._create_entry(self._client, self._username, user_data)

        return self.async_show_form(
            step_id="code",
            data_schema=vol.Schema({vol.Required(CONF_ENTRY_CODE): str}),
            errors=errors,
        )
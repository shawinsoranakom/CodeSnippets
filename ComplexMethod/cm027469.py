async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication dialog."""
        errors: dict[str, str] = {}

        entry = self._get_reauth_entry()

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            if token := user_input.get(CONF_TOKEN):
                ntfy = Ntfy(
                    entry.data[CONF_URL],
                    session,
                    token=user_input[CONF_TOKEN],
                )
            else:
                ntfy = Ntfy(
                    entry.data[CONF_URL],
                    session,
                    username=entry.data[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                )

            try:
                account = await ntfy.account()
                token = (
                    (await ntfy.generate_token("Home Assistant")).token
                    if not user_input.get(CONF_TOKEN)
                    else user_input[CONF_TOKEN]
                )
            except NtfyUnauthorizedAuthenticationError:
                errors["base"] = "invalid_auth"
            except NtfyHTTPError as e:
                _LOGGER.debug("Error %s: %s [%s]", e.code, e.error, e.link)
                errors["base"] = "cannot_connect"
            except NtfyException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if entry.data[CONF_USERNAME] != account.username:
                    return self.async_abort(
                        reason="account_mismatch",
                        description_placeholders={
                            CONF_USERNAME: entry.data[CONF_USERNAME],
                            "wrong_username": account.username,
                        },
                    )
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={CONF_TOKEN: token},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_REAUTH_DATA_SCHEMA, suggested_values=user_input
            ),
            errors=errors,
            description_placeholders={CONF_USERNAME: entry.data[CONF_USERNAME]},
        )
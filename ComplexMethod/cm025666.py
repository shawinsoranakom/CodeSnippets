async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauthentication dialog."""
        errors: dict[str, str] = {}

        entry = (
            self._get_reauth_entry()
            if self.source == SOURCE_REAUTH
            else self._get_reconfigure_entry()
        )

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            try:
                if not await update_namecheapdns(
                    session,
                    entry.data[CONF_HOST],
                    entry.data[CONF_DOMAIN],
                    user_input[CONF_PASSWORD],
                ):
                    errors["base"] = "update_failed"
            except AuthFailed:
                errors["base"] = "invalid_auth"
            except ClientError:
                _LOGGER.debug("Cannot connect", exc_info=True)
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="reauth_confirm" if self.source == SOURCE_REAUTH else "reconfigure",
            data_schema=STEP_RECONFIGURE_DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                "account_panel": f"https://ap.www.namecheap.com/Domains/DomainControlPanel/{entry.data[CONF_DOMAIN]}/advancedns",
                CONF_NAME: entry.title,
                CONF_DOMAIN: entry.data[CONF_DOMAIN],
            },
        )
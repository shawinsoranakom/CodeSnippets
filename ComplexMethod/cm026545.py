async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user, reauth, or reconfigure."""
        errors: dict[str, str] = {}
        if user_input:
            session = async_get_clientsession(self.hass)
            client = TRMNLClient(token=user_input[CONF_API_KEY], session=session)
            try:
                user = await client.get_me()
            except TRMNLAuthenticationError:
                errors["base"] = "invalid_auth"
            except TRMNLError:
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(user.identifier))
                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(),
                        data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                    )
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates={CONF_API_KEY: user_input[CONF_API_KEY]},
                    )
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user.name,
                    data={CONF_API_KEY: user_input[CONF_API_KEY]},
                )
        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_SCHEMA,
            errors=errors,
            description_placeholders={"account_url": TRMNL_ACCOUNT_URL},
        )
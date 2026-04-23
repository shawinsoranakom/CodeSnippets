async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the start of the config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
                description_placeholders={
                    CONF_URL: self._oauth_values.auth_url,
                    CONF_DOCUMENTATION_URL: DOCUMENTATION_URL,
                },
            )

        auth_code = user_input[CONF_AUTH_CODE]

        if auth_code.startswith("="):
            # Sometimes, users may include the "=" from the URL query param; in that
            # case, strip it off and proceed:
            LOGGER.debug('Stripping "=" from the start of the authorization code')
            auth_code = auth_code[1:]

        if len(auth_code) != 45:
            # SimpliSafe authorization codes are 45 characters in length; if the user
            # provides something different, stop them here:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
                errors={CONF_AUTH_CODE: "invalid_auth_code_length"},
                description_placeholders={
                    CONF_URL: self._oauth_values.auth_url,
                    CONF_DOCUMENTATION_URL: DOCUMENTATION_URL,
                },
            )

        errors = {}
        session = aiohttp_client.async_get_clientsession(self.hass)
        try:
            simplisafe = await API.async_from_auth(
                auth_code,
                self._oauth_values.code_verifier,
                session=session,
            )
        except InvalidCredentialsError:
            errors = {CONF_AUTH_CODE: "invalid_auth"}
        except SimplipyError as err:
            LOGGER.error("Unknown error while logging into SimpliSafe: %s", err)
            errors = {"base": "unknown"}

        if errors:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_SCHEMA,
                errors=errors,
                description_placeholders={
                    CONF_URL: self._oauth_values.auth_url,
                    CONF_DOCUMENTATION_URL: DOCUMENTATION_URL,
                },
            )

        simplisafe_user_id = str(simplisafe.user_id)
        data = {CONF_USERNAME: simplisafe_user_id, CONF_TOKEN: simplisafe.refresh_token}

        if self._reauth:
            existing_entry = await self.async_set_unique_id(simplisafe_user_id)
            if not existing_entry:
                # If we don't have an entry that matches this user ID, the user logged
                # in with different credentials:
                return self.async_abort(reason="wrong_account")

            self.hass.config_entries.async_update_entry(
                existing_entry, unique_id=simplisafe_user_id, data=data
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(existing_entry.entry_id)
            )
            return self.async_abort(reason="reauth_successful")

        await self.async_set_unique_id(simplisafe_user_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=simplisafe_user_id, data=data)
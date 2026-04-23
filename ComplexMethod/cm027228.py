async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            # aiopyarr defaults to the service port if one isn't given
            # this is counter to standard practice where http = 80
            # and https = 443.
            if CONF_URL in user_input:
                url = yarl.URL(user_input[CONF_URL])
                user_input[CONF_URL] = f"{url.scheme}://{url.host}:{url.port}{url.path}"

            if self.source == SOURCE_REAUTH:
                user_input = {**self._get_reauth_entry().data, **user_input}

            if CONF_VERIFY_SSL not in user_input:
                user_input[CONF_VERIFY_SSL] = DEFAULT_VERIFY_SSL

            try:
                await _validate_input(self.hass, user_input)
            except ArrAuthenticationException:
                errors = {"base": "invalid_auth"}
            except ArrException:
                errors = {"base": "cannot_connect"}
            except Exception:
                _LOGGER.exception("Unexpected exception")
                return self.async_abort(reason="unknown")
            else:
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data=user_input
                    )

                parsed = yarl.URL(user_input[CONF_URL])

                return self.async_create_entry(
                    title=parsed.host or "Sonarr", data=user_input
                )

        data_schema = self._get_user_data_schema()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )
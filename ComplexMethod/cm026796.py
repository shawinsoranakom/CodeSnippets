async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        def _get_form(
            user_input: Mapping[str, Any], errors: dict[str, str] | None = None
        ) -> ConfigFlowResult:
            """Show the form to the user."""
            url_schema: VolDictType = {}
            if not self._hassio_discovery:
                # Only ask for URL when not discovered
                url_schema[
                    vol.Required(CONF_URL, default=user_input.get(CONF_URL, ""))
                ] = str

            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        **url_schema,
                        vol.Optional(
                            CONF_ADMIN_USERNAME,
                            default=user_input.get(CONF_ADMIN_USERNAME),
                        ): str,
                        vol.Optional(
                            CONF_ADMIN_PASSWORD,
                            default=user_input.get(CONF_ADMIN_PASSWORD, ""),
                        ): str,
                        vol.Optional(
                            CONF_SURVEILLANCE_USERNAME,
                            default=user_input.get(CONF_SURVEILLANCE_USERNAME),
                        ): str,
                        vol.Optional(
                            CONF_SURVEILLANCE_PASSWORD,
                            default=user_input.get(CONF_SURVEILLANCE_PASSWORD, ""),
                        ): str,
                    }
                ),
                errors=errors,
            )

        if user_input is None:
            if self.source == SOURCE_REAUTH:
                return _get_form(self._get_reauth_entry().data)
            return _get_form({})

        if self._hassio_discovery:
            # In case of Supervisor discovery, use pushed URL
            user_input[CONF_URL] = self._hassio_discovery[CONF_URL]

        try:
            # Cannot use cv.url validation in the schema itself, so
            # apply extra validation here.
            cv.url(user_input[CONF_URL])
        except vol.Invalid:
            return _get_form(user_input, {"base": "invalid_url"})

        client = create_motioneye_client(
            user_input[CONF_URL],
            admin_username=user_input.get(CONF_ADMIN_USERNAME),
            admin_password=user_input.get(CONF_ADMIN_PASSWORD),
            surveillance_username=user_input.get(CONF_SURVEILLANCE_USERNAME),
            surveillance_password=user_input.get(CONF_SURVEILLANCE_PASSWORD),
            session=async_get_clientsession(self.hass),
        )

        errors = {}
        try:
            await client.async_client_login()
        except MotionEyeClientConnectionError:
            errors["base"] = "cannot_connect"
        except MotionEyeClientInvalidAuthError:
            errors["base"] = "invalid_auth"
        except MotionEyeClientRequestError:
            errors["base"] = "unknown"
        finally:
            await client.async_client_close()

        if errors:
            return _get_form(user_input, errors)

        if self.source == SOURCE_REAUTH:
            reauth_entry = self._get_reauth_entry()
            # Persist the same webhook id across reauths.
            if CONF_WEBHOOK_ID in reauth_entry.data:
                user_input[CONF_WEBHOOK_ID] = reauth_entry.data[CONF_WEBHOOK_ID]

            return self.async_update_reload_and_abort(reauth_entry, data=user_input)

        # Search for duplicates: there isn't a useful unique_id, but
        # at least prevent entries with the same motionEye URL.
        self._async_abort_entries_match({CONF_URL: user_input[CONF_URL]})

        title = user_input[CONF_URL]
        if self._hassio_discovery:
            title = "App"

        return self.async_create_entry(
            title=title,
            data=user_input,
        )
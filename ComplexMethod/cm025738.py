async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle reconfiguration."""
        reconfigure_entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            api_url = user_input[CONF_API_URL].rstrip("/")
            admin_api_key = user_input[CONF_ADMIN_API_KEY]

            if ":" not in admin_api_key:
                errors["base"] = "invalid_api_key"
            else:
                try:
                    site = await self._validate_credentials(api_url, admin_api_key)
                except GhostAuthError:
                    errors["base"] = "invalid_auth"
                except GhostError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error during Ghost reconfigure")
                    errors["base"] = "unknown"
                else:
                    await self.async_set_unique_id(site["site_uuid"])
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        reconfigure_entry,
                        data_updates={
                            CONF_API_URL: api_url,
                            CONF_ADMIN_API_KEY: admin_api_key,
                        },
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_USER_DATA_SCHEMA,
                suggested_values=user_input or reconfigure_entry.data,
            ),
            errors=errors,
            description_placeholders={"setup_url": GHOST_INTEGRATION_SETUP_URL},
        )
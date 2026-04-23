async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the credentials step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            zeroconf_instance = await zeroconf.async_get_instance(self.hass)
            # unique_id uniquely identifies the registered controller and is used
            # to save the key/certificate pair for each controller separately
            unique_id = self.info["unique_id"]
            assert unique_id
            try:
                result = await self.hass.async_add_executor_job(
                    create_credentials_and_validate,
                    self.hass,
                    self.host,
                    unique_id,
                    user_input,
                    zeroconf_instance,
                )
            except SHCAuthenticationError:
                errors["base"] = "invalid_auth"
            except SHCConnectionError:
                errors["base"] = "cannot_connect"
            except SHCSessionError as err:
                _LOGGER.warning("Session error: %s", err.message)
                errors["base"] = "session_error"
            except SHCRegistrationError as err:
                _LOGGER.warning("Registration error: %s", err.message)
                errors["base"] = "pairing_failed"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                assert result
                entry_data = {
                    # Each host has its own key/certificate pair
                    CONF_SSL_CERTIFICATE: self.hass.config.path(
                        DOMAIN, unique_id, CONF_SHC_CERT
                    ),
                    CONF_SSL_KEY: self.hass.config.path(
                        DOMAIN, unique_id, CONF_SHC_KEY
                    ),
                    CONF_HOST: self.host,
                    CONF_TOKEN: result["token"],
                    CONF_HOSTNAME: result["token"].split(":", 1)[1],
                }
                existing_entry = await self.async_set_unique_id(unique_id)
                if existing_entry:
                    return self.async_update_reload_and_abort(
                        existing_entry,
                        data=entry_data,
                    )

                return self.async_create_entry(
                    title=cast(str, self.info["title"]),
                    data=entry_data,
                )
        else:
            user_input = {}

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                ): str,
            }
        )

        return self.async_show_form(
            step_id="credentials", data_schema=schema, errors=errors
        )
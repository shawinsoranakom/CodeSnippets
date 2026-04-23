async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors = {}
        placeholders = {
            "error": "",
            "troubleshooting_link": "https://www.home-assistant.io/integrations/reolink/#troubleshooting",
        }

        if user_input is not None:
            if CONF_HOST not in user_input:
                user_input[CONF_HOST] = self._host

            # remember input in case of a error
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            self._host = user_input[CONF_HOST]

            host = ReolinkHost(self.hass, user_input, DEFAULT_OPTIONS)
            try:
                if self._disable_privacy:
                    await host.api.baichuan.set_privacy_mode(enable=False)
                    # give the camera some time to startup the HTTP API server
                    await asyncio.sleep(API_STARTUP_TIME)
                await host.async_init()
            except UserNotAdmin:
                errors[CONF_USERNAME] = "not_admin"
                placeholders["username"] = host.api.username
                placeholders["userlevel"] = host.api.user_level
            except PasswordIncompatible:
                errors[CONF_PASSWORD] = "password_incompatible"
                placeholders["special_chars"] = ALLOWED_SPECIAL_CHARS
            except LoginPrivacyModeError:
                self._user_input = user_input
                return await self.async_step_privacy()
            except CredentialsInvalidError:
                errors[CONF_PASSWORD] = "invalid_auth"
            except LoginFirmwareError:
                errors["base"] = "update_needed"
                placeholders["current_firmware"] = host.api.sw_version
                placeholders["needed_firmware"] = (
                    host.api.sw_version_required.version_string
                )
                placeholders["download_center_url"] = (
                    "https://reolink.com/download-center"
                )
            except ApiError as err:
                placeholders["error"] = str(err)
                errors[CONF_HOST] = "api_error"
            except ReolinkWebhookException as err:
                placeholders["error"] = str(err)
                placeholders["more_info"] = (
                    "https://www.home-assistant.io/more-info/no-url-available/#configuring-the-instance-url"
                )
                errors["base"] = "webhook_exception"
            except (ReolinkError, ReolinkException) as err:
                placeholders["error"] = str(err)
                errors[CONF_HOST] = "cannot_connect"
            except Exception as err:
                _LOGGER.exception("Unexpected exception")
                placeholders["error"] = str(err)
                errors[CONF_HOST] = "unknown"
            finally:
                await host.stop()

            if not errors:
                user_input[CONF_PORT] = host.api.port
                user_input[CONF_USE_HTTPS] = host.api.use_https
                user_input[CONF_BC_PORT] = host.api.baichuan.port
                user_input[CONF_BC_ONLY] = host.api.baichuan_only
                user_input[CONF_SUPPORTS_PRIVACY_MODE] = host.api.supported(
                    None, "privacy_mode"
                )

                mac_address = format_mac(host.api.mac_address)
                await self.async_set_unique_id(mac_address, raise_on_progress=False)
                if self.source == SOURCE_REAUTH:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        entry=self._get_reauth_entry(), data=user_input
                    )
                if self.source == SOURCE_RECONFIGURE:
                    self._abort_if_unique_id_mismatch()
                    return self.async_update_reload_and_abort(
                        entry=self._get_reconfigure_entry(), data=user_input
                    )
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=str(host.api.nvr_name),
                    data=user_input,
                    options=DEFAULT_OPTIONS,
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=self._username): str,
                vol.Required(CONF_PASSWORD, default=self._password): str,
            }
        )
        if self._host is None or self.source == SOURCE_RECONFIGURE or errors:
            data_schema = data_schema.extend(
                {
                    vol.Required(CONF_HOST, default=self._host): str,
                }
            )
        if errors:
            data_schema = data_schema.extend(
                {
                    vol.Optional(CONF_PORT): cv.port,
                    vol.Required(CONF_USE_HTTPS, default=False): bool,
                    vol.Required(CONF_BC_PORT, default=DEFAULT_BC_PORT): cv.port,
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders=placeholders,
        )
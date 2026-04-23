async def async_step_encrypted_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the SwitchBot API auth step."""
        errors: dict[str, str] = {}
        assert self._discovered_adv is not None
        description_placeholders: dict[str, str] = {}

        if user_input is None:
            if not self._encryption_method_selected and not (
                self._cloud_username and self._cloud_password
            ):
                return await self.async_step_encrypted_choose_method()
            self._encryption_method_selected = False

        # If we have saved credentials from cloud login, try them first
        if user_input is None and self._cloud_username and self._cloud_password:
            user_input = {
                CONF_USERNAME: self._cloud_username,
                CONF_PASSWORD: self._cloud_password,
            }

        if user_input is not None:
            model: SwitchbotModel = self._discovered_adv.data["modelName"]
            cls = ENCRYPTED_SWITCHBOT_MODEL_TO_CLASS[model]
            try:
                key_details = await cls.async_retrieve_encryption_key(
                    async_get_clientsession(self.hass),
                    self._discovered_adv.address,
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
            except (SwitchbotApiError, SwitchbotAccountConnectionError) as ex:
                _LOGGER.debug(
                    "Failed to connect to SwitchBot API: %s", ex, exc_info=True
                )
                raise AbortFlow(
                    "api_error", description_placeholders={"error_detail": str(ex)}
                ) from ex
            except SwitchbotAuthenticationError as ex:
                _LOGGER.debug("Authentication failed: %s", ex, exc_info=True)
                errors = {"base": "auth_failed"}
                description_placeholders = {"error_detail": str(ex)}
                # Clear saved credentials if auth failed
                self._cloud_username = None
                self._cloud_password = None
            except Exception:
                _LOGGER.exception("Unexpected error retrieving encryption key")
                errors = {"base": "unknown"}
            else:
                return await self.async_step_encrypted_key(key_details)

        user_input = user_input or {}
        return self.async_show_form(
            step_id="encrypted_auth",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME)
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            description_placeholders={
                "name": name_from_discovery(self._discovered_adv),
                **description_placeholders,
            },
        )
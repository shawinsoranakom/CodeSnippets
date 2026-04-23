async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiated flow."""
        user_input = user_input or {}
        errors = {}

        if user_input:
            api = get_api(self.hass, user_input)
            try:
                data: AbstractInfoResponse = await api.async_info()
                data_dict = dataclasses.asdict(data)
                title = data_dict.get(
                    "gogogatename", data_dict.get("ismartgatename", "Cover")
                )
                await self.async_set_unique_id(re.sub("\\..*$", "", data.remoteaccess))
                return self.async_create_entry(title=title, data=user_input)

            except ApiError as api_error:
                device_type = user_input[CONF_DEVICE]
                is_invalid_auth = (
                    device_type == DEVICE_TYPE_GOGOGATE2
                    and api_error.code
                    in (
                        GogoGate2ApiErrorCode.CREDENTIALS_NOT_SET,
                        GogoGate2ApiErrorCode.CREDENTIALS_INCORRECT,
                    )
                ) or (
                    device_type == DEVICE_TYPE_ISMARTGATE
                    and api_error.code
                    in (
                        ISmartGateApiErrorCode.CREDENTIALS_NOT_SET,
                        ISmartGateApiErrorCode.CREDENTIALS_INCORRECT,
                    )
                )

                if is_invalid_auth:
                    errors["base"] = "invalid_auth"
                else:
                    errors["base"] = "cannot_connect"

            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "cannot_connect"

        if self._ip_address and self._device_type:
            self.context["title_placeholders"] = {
                CONF_DEVICE: DEVICE_NAMES[self._device_type],
                CONF_IP_ADDRESS: self._ip_address,
            }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DEVICE,
                        default=self._device_type
                        or user_input.get(CONF_DEVICE, DEVICE_TYPE_GOGOGATE2),
                    ): vol.In((DEVICE_TYPE_GOGOGATE2, DEVICE_TYPE_ISMARTGATE)),
                    vol.Required(
                        CONF_IP_ADDRESS,
                        default=user_input.get(CONF_IP_ADDRESS, self._ip_address),
                    ): str,
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME, "")
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                    ): str,
                }
            ),
            errors=errors,
        )
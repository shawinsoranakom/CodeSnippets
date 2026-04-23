async def async_step_connect(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Connect to a xiaomi miio device."""
        errors: dict[str, str] = {}
        if self.host is None or self.token is None:
            return self.async_abort(reason="incomplete_info")

        if user_input is not None:
            self.model = user_input[CONF_MODEL]

        # Try to connect to a Xiaomi Device.
        connect_device_class = ConnectXiaomiDevice(self.hass)
        try:
            await connect_device_class.async_connect_device(self.host, self.token)
        except AuthException:
            if self.model is None:
                errors["base"] = "wrong_token"
        except SetupException:
            if self.model is None:
                errors["base"] = "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected exception in connect Xiaomi device")
            return self.async_abort(reason="unknown")

        device_info = connect_device_class.device_info

        if self.model is None and device_info is not None:
            self.model = device_info.model

        if self.model is None and not errors:
            errors["base"] = "cannot_connect"

        if errors:
            return self.async_show_form(
                step_id="connect", data_schema=DEVICE_MODEL_CONFIG, errors=errors
            )

        if self.mac is None and device_info is not None:
            self.mac = format_mac(device_info.mac_address)

        unique_id = self.mac
        existing_entry = await self.async_set_unique_id(
            unique_id, raise_on_progress=False
        )
        if existing_entry:
            data = existing_entry.data.copy()
            data[CONF_HOST] = self.host
            data[CONF_TOKEN] = self.token
            if (
                self.cloud_username is not None
                and self.cloud_password is not None
                and self.cloud_country is not None
            ):
                data[CONF_CLOUD_USERNAME] = self.cloud_username
                data[CONF_CLOUD_PASSWORD] = self.cloud_password
                data[CONF_CLOUD_COUNTRY] = self.cloud_country
            return self.async_update_reload_and_abort(existing_entry, data=data)

        if self.name is None:
            self.name = self.model

        flow_type = None
        for gateway_model in MODELS_GATEWAY:
            if self.model.startswith(gateway_model):
                flow_type = CONF_GATEWAY

        if flow_type is None:
            for device_model in MODELS_ALL_DEVICES:
                if self.model.startswith(device_model):
                    flow_type = CONF_DEVICE

        if flow_type is not None:
            return self.async_create_entry(
                title=self.name,
                data={
                    CONF_FLOW_TYPE: flow_type,
                    CONF_HOST: self.host,
                    CONF_TOKEN: self.token,
                    CONF_MODEL: self.model,
                    CONF_MAC: self.mac,
                    CONF_CLOUD_USERNAME: self.cloud_username,
                    CONF_CLOUD_PASSWORD: self.cloud_password,
                    CONF_CLOUD_COUNTRY: self.cloud_country,
                },
            )

        errors["base"] = "unknown_device"
        return self.async_show_form(
            step_id="connect", data_schema=DEVICE_MODEL_CONFIG, errors=errors
        )
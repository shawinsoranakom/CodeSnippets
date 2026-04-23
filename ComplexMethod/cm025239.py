async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a xiaomi miio device through the Miio Cloud."""
        errors = {}
        if user_input is not None:
            if user_input[CONF_MANUAL]:
                return await self.async_step_manual()

            cloud_username = user_input.get(CONF_CLOUD_USERNAME)
            cloud_password = user_input.get(CONF_CLOUD_PASSWORD)
            cloud_country = user_input.get(CONF_CLOUD_COUNTRY)

            if not cloud_username or not cloud_password or not cloud_country:
                errors["base"] = "cloud_credentials_incomplete"
                return self.async_show_form(
                    step_id="cloud",
                    data_schema=DEVICE_CLOUD_CONFIG,
                    errors=errors,
                    description_placeholders=CLOUD_STEP_PLACEHOLDERS,
                )

            miio_cloud = await self.hass.async_add_executor_job(
                MiCloud, cloud_username, cloud_password
            )
            try:
                if not await self.hass.async_add_executor_job(miio_cloud.login):
                    errors["base"] = "cloud_login_error"
            except MiCloudAccessDenied:
                errors["base"] = "cloud_login_error"
            except Exception:
                _LOGGER.exception("Unexpected exception in Miio cloud login")
                return self.async_abort(reason="unknown")

            if errors:
                return self.async_show_form(
                    step_id="cloud",
                    data_schema=DEVICE_CLOUD_CONFIG,
                    errors=errors,
                    description_placeholders=CLOUD_STEP_PLACEHOLDERS,
                )

            try:
                devices_raw = await self.hass.async_add_executor_job(
                    miio_cloud.get_devices, cloud_country
                )
            except Exception:
                _LOGGER.exception("Unexpected exception in Miio cloud get devices")
                return self.async_abort(reason="unknown")

            if not devices_raw:
                errors["base"] = "cloud_no_devices"
                return self.async_show_form(
                    step_id="cloud",
                    data_schema=DEVICE_CLOUD_CONFIG,
                    errors=errors,
                    description_placeholders=CLOUD_STEP_PLACEHOLDERS,
                )

            self.cloud_devices = {}
            for device in devices_raw:
                if not device.get("parent_id"):
                    name = device["name"]
                    model = device["model"]
                    list_name = f"{name} - {model}"
                    self.cloud_devices[list_name] = device

            self.cloud_username = cloud_username
            self.cloud_password = cloud_password
            self.cloud_country = cloud_country

            if self.host is not None:
                for device in self.cloud_devices.values():
                    cloud_host = device.get("localip")
                    if cloud_host == self.host:
                        self.extract_cloud_info(device)
                        return await self.async_step_connect()

            if len(self.cloud_devices) == 1:
                self.extract_cloud_info(list(self.cloud_devices.values())[0])
                return await self.async_step_connect()

            return await self.async_step_select()

        return self.async_show_form(
            step_id="cloud",
            data_schema=DEVICE_CLOUD_CONFIG,
            errors=errors,
            description_placeholders=CLOUD_STEP_PLACEHOLDERS,
        )
async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle user initiated config flow."""
        if user_input is None:
            return await self._async_show_user_form()

        errors = {}

        # Normalize URL
        user_input[CONF_URL] = url_normalize(
            user_input[CONF_URL], default_scheme="http"
        )
        if "://" not in user_input[CONF_URL]:
            errors[CONF_URL] = "invalid_url"
            return await self._async_show_user_form(
                user_input=user_input, errors=errors
            )

        def get_device_info(
            conn: Connection,
        ) -> tuple[GetResponseType, GetResponseType]:
            """Get router info."""
            client = Client(conn)
            try:
                device_info = client.device.information()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not get device.information", exc_info=True)
                try:
                    device_info = client.device.basic_information()
                except Exception:  # noqa: BLE001
                    _LOGGER.debug(
                        "Could not get device.basic_information", exc_info=True
                    )
                    device_info = {}
            try:
                wlan_settings = client.wlan.multi_basic_settings()
            except Exception:  # noqa: BLE001
                _LOGGER.debug("Could not get wlan.multi_basic_settings", exc_info=True)
                wlan_settings = {}
            return device_info, wlan_settings

        conn = await self._connect(user_input, errors)
        if errors:
            return await self._async_show_user_form(
                user_input=user_input, errors=errors
            )
        assert conn

        info, wlan_settings = await self.hass.async_add_executor_job(
            get_device_info, conn
        )
        await self.hass.async_add_executor_job(self._disconnect, conn)

        user_input.update(
            {
                CONF_MAC: get_device_macs(info, wlan_settings),
                CONF_MANUFACTURER: self.manufacturer,
                CONF_UPNP_UDN: self.upnp_udn,
            }
        )

        if not self.unique_id:
            if serial_number := info.get("SerialNumber"):
                await self.async_set_unique_id(serial_number)
                self._abort_if_unique_id_configured(updates=user_input)
            else:
                await self._async_handle_discovery_without_unique_id()

        title = (
            self.context.get("title_placeholders", {}).get(CONF_NAME)
            or info.get("DeviceName")  # device.information
            or info.get("devicename")  # device.basic_information
            or DEFAULT_DEVICE_NAME
        )

        return self.async_create_entry(title=title, data=user_input)
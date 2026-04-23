async def async_step_protocol(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle AlarmDecoder protocol setup."""
        errors = {}
        if user_input is not None:
            if _device_already_added(
                self._async_current_entries(), user_input, self.protocol
            ):
                return self.async_abort(reason="already_configured")
            connection: dict[str, Any] = {}
            baud = None
            device: Device
            if self.protocol == PROTOCOL_SOCKET:
                host = connection[CONF_HOST] = cast(str, user_input[CONF_HOST])
                port = connection[CONF_PORT] = cast(int, user_input[CONF_PORT])
                title: str = f"{host}:{port}"
                device = SocketDevice(interface=(host, port))
            if self.protocol == PROTOCOL_SERIAL:
                path = connection[CONF_DEVICE_PATH] = cast(
                    str, user_input[CONF_DEVICE_PATH]
                )
                baud = connection[CONF_DEVICE_BAUD] = cast(
                    int, user_input[CONF_DEVICE_BAUD]
                )
                title = path
                device = SerialDevice(interface=path)

            controller = AdExt(device)

            def test_connection():
                controller.open(baud)
                controller.close()

            try:
                await self.hass.async_add_executor_job(test_connection)
                return self.async_create_entry(
                    title=title, data={CONF_PROTOCOL: self.protocol, **connection}
                )
            except NoDeviceError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during AlarmDecoder setup")
                errors["base"] = "unknown"

        schema: vol.Schema
        if self.protocol == PROTOCOL_SOCKET:
            schema = vol.Schema(
                {
                    vol.Required(CONF_HOST, default=DEFAULT_DEVICE_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_DEVICE_PORT): int,
                }
            )
        if self.protocol == PROTOCOL_SERIAL:
            schema = vol.Schema(
                {
                    vol.Required(CONF_DEVICE_PATH, default=DEFAULT_DEVICE_PATH): str,
                    vol.Required(CONF_DEVICE_BAUD, default=DEFAULT_DEVICE_BAUD): int,
                }
            )

        return self.async_show_form(
            step_id="protocol",
            data_schema=schema,
            errors=errors,
        )
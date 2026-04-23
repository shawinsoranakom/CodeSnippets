async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            timeout = user_input.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)

            try:
                hello = partial(blk.hello, host, timeout=timeout)
                device = await self.hass.async_add_executor_job(hello)

            except NetworkTimeoutError:
                errors["base"] = "cannot_connect"
                err_msg = "Device not found"

            except OSError as err:
                if err.errno in {errno.EINVAL, socket.EAI_NONAME}:
                    errors["base"] = "invalid_host"
                    err_msg = "Invalid hostname or IP address"
                elif err.errno == errno.ENETUNREACH:
                    errors["base"] = "cannot_connect"
                    err_msg = str(err)
                else:
                    errors["base"] = "unknown"
                    err_msg = str(err)

            else:
                device.timeout = timeout

                if self.source != SOURCE_REAUTH:
                    await self.async_set_device(device)
                    self._abort_if_unique_id_configured(
                        updates={CONF_HOST: device.host[0], CONF_TIMEOUT: timeout}
                    )
                    return await self.async_step_auth()

                if device.mac == self.device.mac:
                    await self.async_set_device(device, raise_on_progress=False)
                    return await self.async_step_auth()

                errors["base"] = "invalid_host"
                err_msg = (
                    "This is not the device you are looking for. The MAC "
                    f"address must be {format_mac(self.device.mac)}"
                )

            _LOGGER.error("Failed to connect to the device at %s: %s", host, err_msg)

            if self.source == SOURCE_IMPORT:
                return self.async_abort(reason=errors["base"])

        data_schema = {
            vol.Required(CONF_HOST): str,
            vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors,
        )
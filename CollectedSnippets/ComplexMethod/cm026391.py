async def async_step_unlock(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Unlock the device.

        The authentication succeeded, but the device is locked.
        We can offer an unlock to prevent authorization errors.
        """
        device = self.device
        errors = {}

        if user_input is None:
            pass

        elif user_input["unlock"]:
            try:
                await self.hass.async_add_executor_job(device.set_lock, False)

            except NetworkTimeoutError as err:
                errors["base"] = "cannot_connect"
                err_msg = str(err)

            except BroadlinkException as err:
                errors["base"] = "unknown"
                err_msg = str(err)

            except OSError as err:
                if err.errno == errno.ENETUNREACH:
                    errors["base"] = "cannot_connect"
                    err_msg = str(err)
                else:
                    errors["base"] = "unknown"
                    err_msg = str(err)

            else:
                return await self.async_step_finish()

            _LOGGER.error(
                "Failed to unlock the device at %s: %s", device.host[0], err_msg
            )

        else:
            return await self.async_step_finish()

        data_schema = {vol.Required("unlock", default=False): bool}
        return self.async_show_form(
            step_id="unlock",
            errors=errors,
            data_schema=vol.Schema(data_schema),
            description_placeholders={
                "name": device.name,
                "model": device.model,
                "host": device.host[0],
            },
        )
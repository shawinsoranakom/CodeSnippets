async def async_step_auth(self) -> ConfigFlowResult:
        """Authenticate to the device."""
        device = self.device
        errors: dict[str, str] = {}

        try:
            await self.hass.async_add_executor_job(device.auth)

        except AuthenticationError:
            errors["base"] = "invalid_auth"
            await self.async_set_unique_id(device.mac.hex())
            return await self.async_step_reset(errors=errors)

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
            await self.async_set_unique_id(device.mac.hex())
            if self.source == SOURCE_IMPORT:
                _LOGGER.warning(
                    (
                        "%s (%s at %s) is ready to be configured. Click "
                        "Configuration in the sidebar, click Integrations and "
                        "click Configure on the device to complete the setup"
                    ),
                    device.name,
                    device.model,
                    device.host[0],
                )

            if device.is_locked:
                return await self.async_step_unlock()
            return await self.async_step_finish()

        await self.async_set_unique_id(device.mac.hex())
        _LOGGER.error(
            "Failed to authenticate to the device at %s: %s", device.host[0], err_msg
        )
        return self.async_show_form(step_id="auth", errors=errors)
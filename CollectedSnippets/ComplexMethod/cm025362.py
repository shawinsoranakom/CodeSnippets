async def async_step_pairing(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the pairing step."""
        errors: dict[str, str] = {}
        assert self._remote is not None

        if user_input is not None:
            pin = user_input[CONF_PIN]
            try:
                await self.hass.async_add_executor_job(
                    partial(self._remote.authorize_pin_code, pincode=pin)
                )
            except SOAPError as err:
                _LOGGER.error("Invalid PIN code: %s", err)
                errors["base"] = ERROR_INVALID_PIN_CODE
            except (URLError, OSError) as err:
                _LOGGER.error("The remote connection was lost: %s", err)
                return self.async_abort(reason="cannot_connect")
            except Exception:
                _LOGGER.exception("Unknown error")
                return self.async_abort(reason="unknown")

            if "base" not in errors:
                encryption_data = {
                    CONF_APP_ID: self._remote.app_id,
                    CONF_ENCRYPTION_KEY: self._remote.enc_key,
                }

                self._data = {**self._data, **encryption_data}

                return self.async_create_entry(
                    title=self._data[CONF_NAME],
                    data=self._data,
                )

        try:
            await self.hass.async_add_executor_job(
                partial(self._remote.request_pin_code, name="Home Assistant")
            )
        except (URLError, SOAPError, OSError) as err:
            _LOGGER.error("The remote connection was lost: %s", err)
            return self.async_abort(reason="cannot_connect")
        except Exception:
            _LOGGER.exception("Unknown error")
            return self.async_abort(reason="unknown")

        return self.async_show_form(
            step_id="pairing",
            data_schema=vol.Schema({vol.Required(CONF_PIN): str}),
            errors=errors,
        )
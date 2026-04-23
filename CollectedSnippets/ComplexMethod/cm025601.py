async def async_step_associate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle associate step."""
        # mypy is not aware that we can't get here without having these set already
        assert self._discovery_info is not None

        if user_input is None:
            return self.async_show_form(
                step_id="associate", data_schema=STEP_ASSOCIATE_SCHEMA
            )

        errors = {}
        if not self._lock:
            self._lock = DKEYLock(self._discovery_info.device)
        lock = self._lock

        try:
            association_data = await lock.associate(user_input["activation_code"])
        except BleakError as err:
            _LOGGER.warning("BleakError", exc_info=err)
            return self.async_abort(reason="cannot_connect")
        except dkey_errors.InvalidActivationCode:
            errors["base"] = "invalid_code"
        except dkey_errors.WrongActivationCode:
            errors["base"] = "wrong_code"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            return self.async_abort(reason="unknown")
        else:
            data = {
                CONF_ADDRESS: self._discovery_info.device.address,
                CONF_ASSOCIATION_DATA: association_data.to_json(),
            }
            if self.source == SOURCE_REAUTH:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data=data
                )

            return self.async_create_entry(
                title=lock.device_info.device_name
                or lock.device_info.device_id
                or lock.name,
                data=data,
            )

        return self.async_show_form(
            step_id="associate", data_schema=STEP_ASSOCIATE_SCHEMA, errors=errors
        )
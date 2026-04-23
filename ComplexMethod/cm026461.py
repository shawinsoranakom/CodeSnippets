async def _async_handle_command(self, command: str, locked: bool) -> None:
        _LOGGER.debug("Lock '%s' is %s", command, "locked" if locked else "unlocked")
        if locked:
            self._attr_is_locking = True
        else:
            self._attr_is_unlocking = True
        self.async_write_ha_state()

        try:
            result = await self.coordinator.context.api.async_execute_command(command)
        except VolvoApiException as ex:
            _LOGGER.debug("Lock '%s' error", command)
            error = self._reset_and_create_error(command, message=ex.message)
            raise error from ex

        status = result.invoke_status if result else ""
        _LOGGER.debug("Lock '%s' result: %s", command, status)

        if status.upper() not in ("COMPLETED", "DELIVERED"):
            error = self._reset_and_create_error(
                command, status=status, message=result.message if result else ""
            )
            raise error

        api_field = cast(
            VolvoCarsValue,
            self.coordinator.get_api_field(self.entity_description.api_field),
        )

        self._attr_is_locking = False
        self._attr_is_unlocking = False

        if locked:
            api_field.value = self.entity_description.api_lock_value
        else:
            api_field.value = self.entity_description.api_unlock_value

        self._attr_is_locked = locked
        self.async_write_ha_state()
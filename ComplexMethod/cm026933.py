async def async_set_alarm(self, command: str, code: str | None = None) -> None:
        """Set alarm."""
        if TYPE_CHECKING:
            assert self.coordinator.yale, "Connection to API is missing"

        try:
            if command == YALE_STATE_ARM_FULL:
                alarm_state = await self.hass.async_add_executor_job(
                    self.coordinator.yale.arm_full
                )
            if command == YALE_STATE_ARM_PARTIAL:
                alarm_state = await self.hass.async_add_executor_job(
                    self.coordinator.yale.arm_partial
                )
            if command == YALE_STATE_DISARM:
                alarm_state = await self.hass.async_add_executor_job(
                    self.coordinator.yale.disarm
                )
        except YALE_ALL_ERRORS as error:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="set_alarm",
                translation_placeholders={
                    "name": self.coordinator.config_entry.title,
                    "error": str(error),
                },
            ) from error

        if alarm_state:
            self.coordinator.data["alarm"] = command
            self.async_write_ha_state()
            return
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="could_not_change_alarm",
        )
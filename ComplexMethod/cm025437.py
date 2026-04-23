async def _async_update_others(self) -> None:
        if not self.available:
            return
        _LOGGER.debug(_UPDATE_MSG, self.name)

        try:
            await self._async_update_unique_id()
        except AmcrestError as error:
            log_update_error(_LOGGER, "update", self.name, "binary sensor", error)
            return

        if not (event_codes := self.entity_description.event_codes):
            raise ValueError(f"Binary sensor {self.name} event codes not set")

        try:
            for event_code in event_codes:
                if await self._api.async_event_channels_happened(event_code):
                    self._attr_is_on = True
                    break
            else:
                self._attr_is_on = False
        except AmcrestError as error:
            log_update_error(_LOGGER, "update", self.name, "binary sensor", error)
            return
async def async_update(self) -> None:
        """Get the latest data and updates the state."""
        if not self.available:
            return
        _LOGGER.debug("Updating %s sensor", self.name)

        sensor_type = self.entity_description.key

        try:
            if self._attr_unique_id is None and (
                serial_number := (await self._api.async_serial_number)
            ):
                self._attr_unique_id = f"{serial_number}-{sensor_type}-{self._channel}"

            if sensor_type == SENSOR_PTZ_PRESET:
                self._attr_native_value = await self._api.async_ptz_presets_count

            elif sensor_type == SENSOR_SDCARD:
                storage = await self._api.async_storage_all
                try:
                    self._attr_extra_state_attributes["Total"] = (
                        f"{storage['total'][0]:.2f} {storage['total'][1]}"
                    )
                except ValueError:
                    self._attr_extra_state_attributes["Total"] = (
                        f"{storage['total'][0]} {storage['total'][1]}"
                    )
                try:
                    self._attr_extra_state_attributes["Used"] = (
                        f"{storage['used'][0]:.2f} {storage['used'][1]}"
                    )
                except ValueError:
                    self._attr_extra_state_attributes["Used"] = (
                        f"{storage['used'][0]} {storage['used'][1]}"
                    )
                try:
                    self._attr_native_value = f"{storage['used_percent']:.2f}"
                except ValueError:
                    self._attr_native_value = storage["used_percent"]
        except AmcrestError as error:
            log_update_error(_LOGGER, "update", self.name, "sensor", error)
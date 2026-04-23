async def async_setup(self) -> None:
        """Set up the tankerkoenig API."""
        for station_id in self._selected_stations:
            try:
                station = await self._tankerkoenig.station_details(station_id)
            except TankerkoenigInvalidKeyError as err:
                _LOGGER.debug(
                    "invalid key error occur during setup of station %s %s",
                    station_id,
                    err,
                )
                raise ConfigEntryAuthFailed(err) from err
            except TankerkoenigConnectionError as err:
                _LOGGER.debug(
                    "connection error occur during setup of station %s %s",
                    station_id,
                    err,
                )
                raise ConfigEntryNotReady(err) from err
            except TankerkoenigError as err:
                _LOGGER.error("Error when adding station %s %s", station_id, err)
                continue

            self.stations[station_id] = station

        entity_reg = er.async_get(self.hass)
        for entity in er.async_entries_for_config_entry(
            entity_reg, self.config_entry.entry_id
        ):
            if entity.unique_id.split("_")[0] not in self._selected_stations:
                _LOGGER.debug("Removing obsolete entity entry %s", entity.entity_id)
                entity_reg.async_remove(entity.entity_id)

        device_reg = dr.async_get(self.hass)
        for device in dr.async_entries_for_config_entry(
            device_reg, self.config_entry.entry_id
        ):
            if not any(
                (ATTR_ID, station_id) in device.identifiers
                for station_id in self._selected_stations
            ):
                _LOGGER.debug("Removing obsolete device entry %s", device.name)
                device_reg.async_update_device(
                    device.id, remove_config_entry_id=self.config_entry.entry_id
                )

        if len(self.stations) > 10:
            _LOGGER.warning(
                "Found more than 10 stations to check. "
                "This might invalidate your api-key on the long run. "
                "Try using a smaller radius"
            )
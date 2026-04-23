async def _async_update_data(self) -> TraccarServerCoordinatorData:
        """Fetch data from Traccar Server."""
        LOGGER.debug("Updating device data")
        data: TraccarServerCoordinatorData = {}
        try:
            (
                devices,
                positions,
                geofences,
            ) = await asyncio.gather(
                self.client.get_devices(),
                self.client.get_positions(),
                self.client.get_geofences(),
            )
        except TraccarAuthenticationException:
            raise ConfigEntryAuthFailed from None
        except TraccarException as ex:
            raise UpdateFailed(f"Error while updating device data: {ex}") from ex

        if TYPE_CHECKING:
            assert isinstance(devices, list[DeviceModel])  # type: ignore[misc]
            assert isinstance(positions, list[PositionModel])  # type: ignore[misc]
            assert isinstance(geofences, list[GeofenceModel])  # type: ignore[misc]

        self._geofences = geofences

        if self.logger.isEnabledFor(LOG_LEVEL_DEBUG):
            self.logger.debug("Received devices: %s", devices)
            self.logger.debug("Received positions: %s", positions)

        for position in positions:
            device_id = position["deviceId"]
            if (device := get_device(device_id, devices)) is None:
                self.logger.debug(
                    "Device %s not found for position: %s",
                    device_id,
                    position["id"],
                )
                continue

            if (
                attr
                := self._return_custom_attributes_if_not_filtered_by_accuracy_configuration(
                    device, position
                )
            ) is None:
                self.logger.debug(
                    "Skipping position update %s for %s due to accuracy filter",
                    position["id"],
                    device_id,
                )
                continue

            data[device_id] = {
                "device": device,
                "geofence": get_first_geofence(
                    geofences,
                    get_geofence_ids(device, position),
                ),
                "position": position,
                "attributes": attr,
            }

        return data
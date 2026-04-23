async def async_initialise(self) -> None:
        """Load available coordinators."""
        self.coordinators = {
            coord.key: RenaultDataUpdateCoordinator(
                self.hass,
                self.config_entry,
                self._hub,
                LOGGER,
                name=f"{self.details.vin} {coord.key}",
                update_method=coord.update_method(self._vehicle),
                update_interval=self._scan_interval,
            )
            for coord in COORDINATORS
            if (
                self.details.supports_endpoint(coord.endpoint)
                and (not coord.requires_electricity or self.details.uses_electricity())
            )
        }
        # Check all coordinators
        await asyncio.gather(
            *(
                coordinator.async_config_entry_first_refresh()
                for coordinator in self.coordinators.values()
            )
        )
        for key in list(self.coordinators):
            # list() to avoid Runtime iteration error
            coordinator = self.coordinators[key]
            if coordinator.not_supported:
                # Remove endpoint as it is not supported for this vehicle.
                LOGGER.warning(
                    "Ignoring endpoint %s as it is not supported: %s",
                    coordinator.name,
                    coordinator.last_exception,
                )
                del self.coordinators[key]
            elif coordinator.access_denied:
                # Remove endpoint as it is denied for this vehicle.
                LOGGER.warning(
                    "Ignoring endpoint %s as it is denied: %s",
                    coordinator.name,
                    coordinator.last_exception,
                )
                del self.coordinators[key]
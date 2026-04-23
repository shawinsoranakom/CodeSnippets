def _async_update_attrs(self) -> None:
        """Update the attributes of the entity."""

        # Supported Features - only show install button if update is available
        # but not already scheduled
        if self.scoped and self._value == AVAILABLE:
            self._attr_supported_features = (
                UpdateEntityFeature.PROGRESS | UpdateEntityFeature.INSTALL
            )
        else:
            self._attr_supported_features = UpdateEntityFeature.PROGRESS

        # Installed Version
        self._attr_installed_version = self.get("vehicle_state_car_version")
        if self._attr_installed_version is not None:
            # Remove build from version
            self._attr_installed_version = self._attr_installed_version.split(" ")[0]

        # Latest Version - hide update if scheduled far in the future
        if self._value in (AVAILABLE, INSTALLING, DOWNLOADING, WIFI_WAIT) or (
            self._value == SCHEDULED and self._is_scheduled_soon()
        ):
            self._attr_latest_version = self.coordinator.data[
                "vehicle_state_software_update_version"
            ]
        else:
            self._attr_latest_version = self._attr_installed_version

        # In Progress - only show as installing if actually installing or
        # scheduled to start within 2 minutes
        if self._value == INSTALLING:
            self._attr_in_progress = True
            if install_perc := self.get("vehicle_state_software_update_install_perc"):
                self._attr_update_percentage = install_perc
        elif self._value == SCHEDULED and self._is_scheduled_soon():
            self._attr_in_progress = True
            self._attr_update_percentage = None
        else:
            self._attr_in_progress = False
            self._attr_update_percentage = None
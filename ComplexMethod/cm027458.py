async def _fetch_device_configuration(self) -> None:
        """Fetch initial device config."""
        self.network = self.dsm.network
        await self.network.update()

        if self._with_file_station:
            LOGGER.debug(
                "Enable file station api updates for '%s'", self._entry.unique_id
            )
            self.file_station = self.dsm.file

        if self._with_security:
            LOGGER.debug("Enable security api updates for '%s'", self._entry.unique_id)
            self.security = self.dsm.security

        if self._with_photos:
            LOGGER.debug("Enable photos api updates for '%s'", self._entry.unique_id)
            self.photos = self.dsm.photos

        if self._with_storage:
            LOGGER.debug("Enable storage api updates for '%s'", self._entry.unique_id)
            self.storage = self.dsm.storage

        if self._with_upgrade:
            LOGGER.debug("Enable upgrade api updates for '%s'", self._entry.unique_id)
            self.upgrade = self.dsm.upgrade

        if self._with_system:
            LOGGER.debug("Enable system api updates for '%s'", self._entry.unique_id)
            self.system = self.dsm.system

        if self._with_utilisation:
            LOGGER.debug(
                "Enable utilisation api updates for '%s'", self._entry.unique_id
            )
            self.utilisation = self.dsm.utilisation

        if self._with_surveillance_station:
            LOGGER.debug(
                "Enable surveillance_station api updates for '%s'",
                self._entry.unique_id,
            )
            self.surveillance_station = self.dsm.surveillance_station

        if self._with_external_usb:
            LOGGER.debug(
                "Enable external usb api updates for '%s'", self._entry.unique_id
            )
            self.external_usb = self.dsm.external_usb
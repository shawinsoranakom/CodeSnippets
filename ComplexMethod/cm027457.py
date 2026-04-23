def _setup_api_requests(self) -> None:
        """Determine if we should fetch each API, if one entity needs it."""
        # Entities not added yet, fetch all
        if not self._fetching_entities:
            LOGGER.debug(
                "Entities not added yet, fetch all for '%s'", self._entry.unique_id
            )
            return

        # surveillance_station is updated by own coordinator
        if self.surveillance_station:
            self.dsm.reset(self.surveillance_station)

        # Determine if we should fetch an API
        self._with_system = bool(self.dsm.apis.get(SynoCoreSystem.API_KEY))
        self._with_security = bool(
            self._fetching_entities.get(SynoCoreSecurity.API_KEY)
        )
        self._with_storage = bool(self._fetching_entities.get(SynoStorage.API_KEY))
        self._with_photos = bool(self._fetching_entities.get(SynoStorage.API_KEY))
        self._with_upgrade = bool(self._fetching_entities.get(SynoCoreUpgrade.API_KEY))
        self._with_utilisation = bool(
            self._fetching_entities.get(SynoCoreUtilization.API_KEY)
        )
        self._with_information = bool(
            self._fetching_entities.get(SynoDSMInformation.API_KEY)
        )
        self._with_external_usb = bool(
            self._fetching_entities.get(SynoCoreExternalUSB.API_KEY)
        )

        # Reset not used API, information is not reset since it's used in device_info
        if not self._with_security:
            LOGGER.debug(
                "Disable security api from being updated for '%s'",
                self._entry.unique_id,
            )
            if self.security:
                self.dsm.reset(self.security)
            self.security = None

        if not self._with_file_station:
            LOGGER.debug(
                "Disable file station api from being updated or '%s'",
                self._entry.unique_id,
            )
            if self.file_station:
                self.dsm.reset(self.file_station)
            self.file_station = None

        if not self._with_photos:
            LOGGER.debug(
                "Disable photos api from being updated or '%s'", self._entry.unique_id
            )
            if self.photos:
                self.dsm.reset(self.photos)
            self.photos = None

        if not self._with_storage:
            LOGGER.debug(
                "Disable storage api from being updatedf or '%s'", self._entry.unique_id
            )
            if self.storage:
                self.dsm.reset(self.storage)
            self.storage = None

        if not self._with_system:
            LOGGER.debug(
                "Disable system api from being updated for '%s'", self._entry.unique_id
            )
            if self.system:
                self.dsm.reset(self.system)
            self.system = None

        if not self._with_upgrade:
            LOGGER.debug(
                "Disable upgrade api from being updated for '%s'", self._entry.unique_id
            )
            if self.upgrade:
                self.dsm.reset(self.upgrade)
            self.upgrade = None

        if not self._with_utilisation:
            LOGGER.debug(
                "Disable utilisation api from being updated for '%s'",
                self._entry.unique_id,
            )
            if self.utilisation:
                self.dsm.reset(self.utilisation)
            self.utilisation = None

        if not self._with_external_usb:
            LOGGER.debug(
                "Disable external usb api from being updated for '%s'",
                self._entry.unique_id,
            )
            if self.external_usb:
                self.dsm.reset(self.external_usb)
            self.external_usb = None
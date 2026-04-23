async def async_setup(self) -> None:
        """Start interacting with the NAS."""
        session = async_get_clientsession(self._hass, self._entry.data[CONF_VERIFY_SSL])
        self.dsm = SynologyDSM(
            session,
            self._entry.data[CONF_HOST],
            self._entry.data[CONF_PORT],
            self._entry.data[CONF_USERNAME],
            self._entry.data[CONF_PASSWORD],
            self._entry.data[CONF_SSL],
            timeout=DEFAULT_TIMEOUT,
            device_token=self._entry.data.get(CONF_DEVICE_TOKEN),
        )
        await self.async_login()

        self.information = self.dsm.information
        await self.information.update()

        # check if surveillance station is used
        self._with_surveillance_station = bool(
            self.dsm.apis.get(SynoSurveillanceStation.CAMERA_API_KEY)
        )
        if self._with_surveillance_station:
            try:
                await self.dsm.surveillance_station.update()
            except SYNOLOGY_CONNECTION_EXCEPTIONS:
                self._with_surveillance_station = False
                self.dsm.reset(SynoSurveillanceStation.API_KEY)
                LOGGER.warning(
                    "Surveillance Station found, but disabled due to missing user"
                    " permissions"
                )

        LOGGER.debug(
            "State of Surveillance_station during setup of '%s': %s",
            self._entry.unique_id,
            self._with_surveillance_station,
        )

        # check if upgrade is available
        try:
            await self.dsm.upgrade.update()
        except SYNOLOGY_CONNECTION_EXCEPTIONS as ex:
            self._with_upgrade = False
            self.dsm.reset(SynoCoreUpgrade.API_KEY)
            LOGGER.debug("Disabled fetching upgrade data during setup: %s", ex)

        # check if file station is used and permitted
        self._with_file_station = bool(
            self.information.awesome_version >= AwesomeVersion("6.0")
            and self.dsm.apis.get(SynoFileStation.LIST_API_KEY)
        )
        if self._with_file_station:
            shares: list | None = None
            with suppress(*SYNOLOGY_CONNECTION_EXCEPTIONS):
                shares = await self.dsm.file.get_shared_folders(only_writable=True)
            if not shares:
                self._with_file_station = False
                self.dsm.reset(SynoFileStation.API_KEY)
                LOGGER.debug(
                    "File Station found, but disabled due to missing user"
                    " permissions or no writable shared folders available"
                )

            if shares and not self._entry.options.get(CONF_BACKUP_PATH):
                ir.async_create_issue(
                    self._hass,
                    DOMAIN,
                    f"{ISSUE_MISSING_BACKUP_SETUP}_{self._entry.unique_id}",
                    data={"entry_id": self._entry.entry_id},
                    is_fixable=True,
                    is_persistent=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=ISSUE_MISSING_BACKUP_SETUP,
                    translation_placeholders={"title": self._entry.title},
                )

        LOGGER.debug(
            "State of File Station during setup of '%s': %s",
            self._entry.unique_id,
            self._with_file_station,
        )

        await self._fetch_device_configuration()

        try:
            await self._update()
        except SYNOLOGY_CONNECTION_EXCEPTIONS as err:
            LOGGER.debug(
                "Connection error during setup of '%s' with exception: %s",
                self._entry.unique_id,
                err,
            )
            raise
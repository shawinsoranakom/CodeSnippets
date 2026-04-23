async def _install_firmware(
        self,
        fw_update_url: str,
        fw_type: str,
        firmware_name: str,
        expected_installed_firmware_type: ApplicationType,
    ) -> None:
        """Install firmware."""
        assert self._device is not None

        # Keep track of the firmware we're working with, for error messages
        self.installing_firmware_name = firmware_name

        # For the duration of firmware flashing, hint to other integrations (i.e. ZHA)
        # that the hardware is in use and should not be accessed. This is separate from
        # locking the serial port itself, since a momentary release of the port may
        # still allow for ZHA to reclaim the device.
        async with async_firmware_flashing_context(self.hass, self._device, DOMAIN):
            # Installing new firmware is only truly required if the wrong type is
            # installed: upgrading to the latest release of the current firmware type
            # isn't strictly necessary for functionality.
            self._probed_firmware_info = await probe_silabs_firmware_info(
                self._device,
                flasher_cls=self._flasher_cls,
            )

            firmware_install_required = self._probed_firmware_info is None or (
                self._probed_firmware_info.firmware_type
                != expected_installed_firmware_type
            )

            session = async_get_clientsession(self.hass)
            client = FirmwareUpdateClient(fw_update_url, session)

            try:
                manifest = await client.async_update_data()
                fw_manifest = next(
                    fw for fw in manifest.firmwares if fw.filename.startswith(fw_type)
                )
            except (StopIteration, TimeoutError, ClientError, ManifestMissing) as err:
                _LOGGER.warning(
                    "Failed to fetch firmware update manifest", exc_info=True
                )

                # Not having internet access should not prevent setup
                if not firmware_install_required:
                    _LOGGER.debug(
                        "Skipping firmware upgrade due to index download failure"
                    )
                    return

                raise AbortFlow(
                    reason="fw_download_failed",
                    description_placeholders=self._get_translation_placeholders(),
                ) from err

            if not firmware_install_required:
                assert self._probed_firmware_info is not None

                # Make sure we do not downgrade the firmware
                fw_metadata = NabuCasaMetadata.from_json(fw_manifest.metadata)
                fw_version = fw_metadata.get_public_version()
                probed_fw_version = Version(self._probed_firmware_info.firmware_version)

                if probed_fw_version >= fw_version:
                    _LOGGER.debug(
                        "Not downgrading firmware, installed %s is newer than available %s",
                        probed_fw_version,
                        fw_version,
                    )
                    return

            try:
                fw_data = await client.async_fetch_firmware(fw_manifest)
            except (TimeoutError, ClientError, ValueError) as err:
                _LOGGER.warning("Failed to fetch firmware update", exc_info=True)

                # If we cannot download new firmware, we shouldn't block setup
                if not firmware_install_required:
                    _LOGGER.debug(
                        "Skipping firmware upgrade due to image download failure"
                    )
                    return

                # Otherwise, fail
                raise AbortFlow(
                    reason="fw_download_failed",
                    description_placeholders=self._get_translation_placeholders(),
                ) from err

            self._probed_firmware_info = await async_flash_silabs_firmware(
                hass=self.hass,
                device=self._device,
                fw_data=fw_data,
                flasher_cls=self._flasher_cls,
                expected_installed_firmware_type=expected_installed_firmware_type,
                progress_callback=lambda offset, total: self.async_update_progress(
                    offset / total
                ),
            )
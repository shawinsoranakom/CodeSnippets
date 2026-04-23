def _update_attributes(self) -> None:
        """Recompute the attributes of the entity."""
        self._attr_title = self.entity_description.firmware_name or "Unknown"

        if (
            self._current_firmware_info is None
            or self._current_firmware_info.firmware_version is None
        ):
            self._attr_installed_version = None
        else:
            self._attr_installed_version = self.entity_description.version_parser(
                self._current_firmware_info.firmware_version
            )

        self._latest_firmware = None
        self._attr_latest_version = None
        self._attr_release_summary = None
        self._attr_release_url = None

        if (
            self._latest_manifest is None
            or self.entity_description.fw_type is None
            or self.entity_description.version_key is None
        ):
            return

        try:
            self._latest_firmware = next(
                f
                for f in self._latest_manifest.firmwares
                if f.filename.startswith(self.entity_description.fw_type)
            )
        except StopIteration:
            pass
        else:
            version = cast(
                str, self._latest_firmware.metadata[self.entity_description.version_key]
            )
            self._attr_latest_version = self.entity_description.version_parser(version)
            self._attr_release_summary = self._latest_firmware.release_notes
            self._attr_release_url = str(self._latest_manifest.html_url)
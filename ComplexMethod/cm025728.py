async def async_install(
        self, version: str | None, backup: bool, **kwargs: Any
    ) -> None:
        """Install a new software version."""

        if not self.get_matter_attribute_value(
            clusters.OtaSoftwareUpdateRequestor.Attributes.UpdatePossible
        ):
            raise HomeAssistantError("Device is not ready to install updates")

        software_version: str | int | None = version
        if self._software_update is not None and (
            version is None
            or version
            in {
                self._software_update.software_version_string,
                self._attr_latest_version,
            }
        ):
            # Update to the version previously fetched and shown.
            # We can pass the integer version directly to speedup download.
            software_version = self._software_update.software_version

        if software_version is None:
            raise HomeAssistantError("No software version specified")

        self._attr_in_progress = True
        # Immediately update the progress state change to make frontend feel responsive.
        # Progress updates from the device usually take few seconds to come in.
        self.async_write_ha_state()
        try:
            await self.matter_client.update_node(
                node_id=self._endpoint.node.node_id,
                software_version=software_version,
            )
        except UpdateCheckError as err:
            raise HomeAssistantError(f"Error finding applicable update: {err}") from err
        except UpdateError as err:
            raise HomeAssistantError(f"Error updating: {err}") from err
        finally:
            # Check for updates right after the update since Matter devices
            # can have strict update paths (e.g. Eve)
            self._cancel_update = async_call_later(
                self.hass, POLL_AFTER_INSTALL, self._async_update_future
            )
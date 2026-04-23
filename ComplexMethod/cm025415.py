async def async_step_hassio(
        self, discovery_info: HassioServiceInfo
    ) -> ConfigFlowResult:
        """Handle hassio discovery."""
        config = discovery_info.config
        url = f"http://{config['host']}:{config['port']}"
        config_entry_data = {"url": url}

        if current_entries := self._async_current_entries():
            for current_entry in current_entries:
                if current_entry.source != SOURCE_HASSIO:
                    continue
                current_url = yarl.URL(current_entry.data["url"])
                if not (unique_id := current_entry.unique_id):
                    # The first version did not set a unique_id
                    # so if the entry does not have a unique_id
                    # we have to assume it's the first version
                    # This check can be removed in HA Core 2025.9
                    unique_id = discovery_info.uuid

                if unique_id != discovery_info.uuid:
                    continue

                if (
                    current_url.host != config["host"]
                    or current_url.port == config["port"]
                ):
                    # Reload the entry since OTBR has restarted
                    if current_entry.state == ConfigEntryState.LOADED:
                        assert current_entry.unique_id is not None
                        await self.hass.config_entries.async_reload(
                            current_entry.entry_id
                        )

                    continue

                # Update URL with the new port
                self.hass.config_entries.async_update_entry(
                    current_entry,
                    data=config_entry_data,
                    unique_id=unique_id,  # Remove in HA Core 2025.9
                )
                return self.async_abort(reason="already_configured")

        try:
            await self._connect_and_configure_router(url)
        except AlreadyConfigured:
            return self.async_abort(reason="already_configured")
        except (
            python_otbr_api.OTBRError,
            aiohttp.ClientError,
            TimeoutError,
        ) as exc:
            _LOGGER.warning("Failed to communicate with OTBR@%s: %s", url, exc)
            return self.async_abort(reason="unknown")

        await self.async_set_unique_id(discovery_info.uuid)
        return self.async_create_entry(
            title=await _title(self.hass, discovery_info),
            data=config_entry_data,
        )
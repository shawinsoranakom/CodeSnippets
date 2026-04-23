def _handle_config_entry_removed(
        self,
        entry: config_entries.ConfigEntry,
    ) -> None:
        """Handle config entry changes."""
        if TYPE_CHECKING:
            assert self._description_cache is not None
        cache = self._description_cache
        for discovery_key in entry.discovery_keys[DOMAIN]:
            if discovery_key.version != 1 or not isinstance(discovery_key.key, str):
                continue
            udn = discovery_key.key
            _LOGGER.debug("Rediscover service %s", udn)

            for ssdp_device in self._ssdp_devices:
                if ssdp_device.udn != udn:
                    continue
                for dst in ssdp_device.all_combined_headers:
                    has_cached_desc, info_desc = cache.peek_description_dict(
                        ssdp_device.location
                    )
                    if has_cached_desc and info_desc:
                        self._ssdp_listener_process_callback(
                            ssdp_device,
                            dst,
                            SsdpSource.SEARCH,
                            info_desc,
                            True,  # Skip integration callbacks
                        )
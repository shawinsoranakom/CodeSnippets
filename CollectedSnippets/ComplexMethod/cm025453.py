def _handle_metadata_update() -> None:
        """Handle metadata coordinator update - detect subscription changes."""
        data = metadata_coordinator.data
        if not data:
            return

        current_vins, current_site_ids = _get_subscribed_ids_from_metadata(data)

        added_vins = current_vins - known_vins
        removed_vins = known_vins - current_vins
        added_sites = current_site_ids - known_site_ids
        removed_sites = known_site_ids - current_site_ids

        if added_vins or removed_vins or added_sites or removed_sites:
            LOGGER.info(
                "Tesla subscription changes detected "
                "(added vehicles: %s, removed vehicles: %s, "
                "added energy sites: %s, removed energy sites: %s), "
                "reloading integration",
                added_vins or "none",
                removed_vins or "none",
                added_sites or "none",
                removed_sites or "none",
            )
            hass.config_entries.async_schedule_reload(entry.entry_id)
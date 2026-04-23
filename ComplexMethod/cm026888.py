async def async_migrate_entry(
    hass: HomeAssistant, config_entry: WLEDConfigEntry
) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(
        "Migrating configuration from version %s.%s",
        config_entry.version,
        config_entry.minor_version,
    )

    if config_entry.version > 1:
        # The user has downgraded from a future version
        return False

    if config_entry.version == 1:
        if config_entry.minor_version < 2:
            # 1.2: Normalize unique ID to be lowercase MAC address without separators.
            # This matches the format used by WLED firmware.
            if TYPE_CHECKING:
                assert config_entry.unique_id
            normalized_mac_address = normalize_mac_address(config_entry.unique_id)
            duplicate_entries = [
                entry
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.unique_id
                and normalize_mac_address(entry.unique_id) == normalized_mac_address
            ]
            ignored_entries = [
                entry
                for entry in duplicate_entries
                if entry.entry_id != config_entry.entry_id
                and entry.source == SOURCE_IGNORE
            ]
            if ignored_entries:
                _LOGGER.info(
                    "Found %d ignored WLED config entries with the same MAC address, removing them",
                    len(ignored_entries),
                )
                await asyncio.gather(
                    *[
                        hass.config_entries.async_remove(entry.entry_id)
                        for entry in ignored_entries
                    ]
                )
            if len(duplicate_entries) - len(ignored_entries) > 1:
                _LOGGER.warning(
                    "Found multiple WLED config entries with the same MAC address, cannot migrate to version 1.2"
                )
                return False

            hass.config_entries.async_update_entry(
                config_entry,
                unique_id=normalized_mac_address,
                version=1,
                minor_version=2,
            )

    _LOGGER.debug(
        "Migration to configuration version %s.%s successful",
        config_entry.version,
        config_entry.minor_version,
    )

    return True
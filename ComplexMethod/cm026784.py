async def handle_get_torrents(service_call: ServiceCall) -> dict[str, Any] | None:
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(service_call.data[ATTR_DEVICE_ID])

        if device_entry is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_device",
                translation_placeholders={
                    "device_id": service_call.data[ATTR_DEVICE_ID]
                },
            )

        entry_id = None

        for key, value in device_entry.identifiers:
            if key == DOMAIN:
                entry_id = value
                break
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_entry_id",
                translation_placeholders={"device_id": entry_id or ""},
            )

        entry: QBittorrentConfigEntry | None = hass.config_entries.async_get_entry(
            entry_id
        )
        if entry is None or entry.state != ConfigEntryState.LOADED:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_entry_id",
                translation_placeholders={"device_id": entry_id},
            )
        coordinator = entry.runtime_data
        items = await coordinator.get_torrents(service_call.data[TORRENT_FILTER])
        info = format_torrents(items)
        return {
            STATE_ATTR_TORRENTS: info,
        }
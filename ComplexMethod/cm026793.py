async def handle_speaker_hub_play_call(service_call: ServiceCall) -> None:
        """Handle Speaker Hub audio play call."""
        service_data = service_call.data
        device_registry = dr.async_get(hass)
        device_entry = device_registry.async_get(service_data[ATTR_TARGET_DEVICE])
        if device_entry is not None:
            for entry_id in device_entry.config_entries:
                if (entry := hass.config_entries.async_get_entry(entry_id)) is None:
                    continue
                if entry.domain == DOMAIN:
                    break
            if entry is None or entry.state != ConfigEntryState.LOADED:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_config_entry",
                )
            home_store = entry.runtime_data
            for identifier in device_entry.identifiers:
                if (
                    device_coordinator := home_store.device_coordinators.get(
                        identifier[1]
                    )
                ) is not None:
                    params = {
                        ATTR_TEXT_MESSAGE: service_data[ATTR_TEXT_MESSAGE],
                        ATTR_REPEAT: service_data[ATTR_REPEAT],
                    }

                    for attr, transform in _SPEAKER_HUB_PLAY_CALL_OPTIONAL_ATTRS:
                        if attr in service_data:
                            params[attr] = transform(service_data[attr])

                    play_request = ClientRequest("playAudio", params)
                    await device_coordinator.device.call_device(play_request)
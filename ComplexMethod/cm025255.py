async def _async_dial(service_call: ServiceCall) -> None:
    """Call Fritz dial service."""
    target_entry_ids = await async_extract_config_entry_ids(service_call)
    target_entries: list[FritzConfigEntry] = [
        loaded_entry
        for loaded_entry in service_call.hass.config_entries.async_loaded_entries(
            DOMAIN
        )
        if loaded_entry.entry_id in target_entry_ids
    ]

    if not target_entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="config_entry_not_found",
            translation_placeholders={"service": service_call.service},
        )

    for target_entry in target_entries:
        _LOGGER.debug("Executing service %s", service_call.service)
        avm_wrapper = target_entry.runtime_data
        try:
            await avm_wrapper.async_trigger_dial(
                service_call.data["number"],
                max_ring_seconds=service_call.data["max_ring_seconds"],
            )
        except (FritzServiceError, FritzActionError) as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="service_parameter_unknown"
            ) from ex
        except FritzActionFailedError as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="service_dial_failed"
            ) from ex
        except FritzConnectionException as ex:
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="service_not_supported"
            ) from ex
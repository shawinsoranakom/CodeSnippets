def _get_custom_equivalent_units(
    hass: HomeAssistant,
) -> dict[str, dict[str | None, str]]:
    """Check whether any integration supplies custom equivalent units for its entities."""
    custom_equivalent_units_per_entity: dict[str, dict[str | None, str]] = {}
    for domain, platform in hass.data[DATA_RECORDER].recorder_platforms.items():
        custom_equivalent_units = getattr(
            platform, INTEGRATION_PLATFORM_CUSTOM_EQUIVALENT_UNITS, None
        )

        if not custom_equivalent_units:
            continue

        try:
            platform_custom_equivalent_units = run_callback_threadsafe(
                hass.loop, custom_equivalent_units, hass
            ).result()
        except Exception as exc:  # noqa: BLE001
            if domain not in _warn_custom_units_error:
                _warn_custom_units_error.add(domain)
                _LOGGER.warning(
                    "Error calling %s for recorder platform domain %s: %s",
                    INTEGRATION_PLATFORM_CUSTOM_EQUIVALENT_UNITS,
                    domain,
                    exc,
                )
            continue

        if not platform_custom_equivalent_units:
            continue

        try:
            validated_data = CUSTOM_EQUIVALENT_UNITS_SCHEMA(
                platform_custom_equivalent_units
            )
            custom_equivalent_units_per_entity |= validated_data
        except vol.Invalid as inv:
            if domain not in _warn_custom_units_error:
                _warn_custom_units_error.add(domain)
                _LOGGER.warning(
                    "Error processing result of %s for recorder platform domain %s: %s for object: %s",
                    INTEGRATION_PLATFORM_CUSTOM_EQUIVALENT_UNITS,
                    domain,
                    inv,
                    platform_custom_equivalent_units,
                )

    return custom_equivalent_units_per_entity
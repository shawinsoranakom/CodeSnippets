def _validate_grid_source(
    hass: HomeAssistant,
    source: data.GridSourceType,
    statistics_metadata: dict[str, tuple[int, recorder.models.StatisticMetaData]],
    wanted_statistics_metadata: set[str],
    source_result: ValidationIssues,
    validate_calls: list[functools.partial[None]],
) -> None:
    """Validate grid energy source (unified format)."""
    stat_energy_from = source.get("stat_energy_from")
    stat_energy_to = source.get("stat_energy_to")
    stat_rate = source.get("stat_rate")

    # Validate import meter (optional)
    if stat_energy_from:
        wanted_statistics_metadata.add(stat_energy_from)
        validate_calls.append(
            functools.partial(
                _async_validate_usage_stat,
                hass,
                statistics_metadata,
                stat_energy_from,
                ENERGY_USAGE_DEVICE_CLASSES,
                ENERGY_USAGE_UNITS,
                ENERGY_UNIT_ERROR,
                source_result,
            )
        )

        # Validate import cost tracking (only if import meter exists)
        if (stat_cost := source.get("stat_cost")) is not None:
            wanted_statistics_metadata.add(stat_cost)
            validate_calls.append(
                functools.partial(
                    _async_validate_cost_stat,
                    hass,
                    statistics_metadata,
                    stat_cost,
                    source_result,
                )
            )
        elif (entity_energy_price := source.get("entity_energy_price")) is not None:
            validate_calls.append(
                functools.partial(
                    _async_validate_price_entity,
                    hass,
                    entity_energy_price,
                    source_result,
                    ENERGY_PRICE_UNITS,
                    ENERGY_PRICE_UNIT_ERROR,
                )
            )

        if (
            source.get("entity_energy_price") is not None
            or source.get("number_energy_price") is not None
        ):
            validate_calls.append(
                functools.partial(
                    _async_validate_auto_generated_cost_entity,
                    hass,
                    stat_energy_from,
                    source_result,
                )
            )

    # Validate export meter (optional)
    if stat_energy_to:
        wanted_statistics_metadata.add(stat_energy_to)
        validate_calls.append(
            functools.partial(
                _async_validate_usage_stat,
                hass,
                statistics_metadata,
                stat_energy_to,
                ENERGY_USAGE_DEVICE_CLASSES,
                ENERGY_USAGE_UNITS,
                ENERGY_UNIT_ERROR,
                source_result,
            )
        )

        # Validate export compensation tracking
        if (stat_compensation := source.get("stat_compensation")) is not None:
            wanted_statistics_metadata.add(stat_compensation)
            validate_calls.append(
                functools.partial(
                    _async_validate_cost_stat,
                    hass,
                    statistics_metadata,
                    stat_compensation,
                    source_result,
                )
            )
        elif (
            entity_price_export := source.get("entity_energy_price_export")
        ) is not None:
            validate_calls.append(
                functools.partial(
                    _async_validate_price_entity,
                    hass,
                    entity_price_export,
                    source_result,
                    ENERGY_PRICE_UNITS,
                    ENERGY_PRICE_UNIT_ERROR,
                )
            )

        if (
            source.get("entity_energy_price_export") is not None
            or source.get("number_energy_price_export") is not None
        ):
            validate_calls.append(
                functools.partial(
                    _async_validate_auto_generated_cost_entity,
                    hass,
                    stat_energy_to,
                    source_result,
                )
            )

    # Validate power sensor (optional)
    if stat_rate:
        wanted_statistics_metadata.add(stat_rate)
        validate_calls.append(
            functools.partial(
                _async_validate_power_stat,
                hass,
                statistics_metadata,
                stat_rate,
                POWER_USAGE_DEVICE_CLASSES,
                POWER_USAGE_UNITS,
                POWER_UNIT_ERROR,
                source_result,
            )
        )
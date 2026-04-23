async def async_validate(hass: HomeAssistant) -> EnergyPreferencesValidation:
    """Validate the energy configuration."""
    manager: data.EnergyManager = await data.async_get_manager(hass)
    statistics_metadata: dict[str, tuple[int, recorder.models.StatisticMetaData]] = {}
    validate_calls: list[functools.partial[None]] = []
    wanted_statistics_metadata: set[str] = set()

    result = EnergyPreferencesValidation()

    if manager.data is None:
        return result

    # Create a list of validation checks
    for source in manager.data["energy_sources"]:
        source_result = ValidationIssues()
        result.energy_sources.append(source_result)

        if source["type"] == "grid":
            _validate_grid_source(
                hass,
                source,
                statistics_metadata,
                wanted_statistics_metadata,
                source_result,
                validate_calls,
            )

        elif source["type"] == "gas":
            _validate_gas_source(
                hass,
                source,
                statistics_metadata,
                wanted_statistics_metadata,
                source_result,
                validate_calls,
            )

        elif source["type"] == "water":
            _validate_water_source(
                hass,
                source,
                statistics_metadata,
                wanted_statistics_metadata,
                source_result,
                validate_calls,
            )

        elif source["type"] == "solar":
            wanted_statistics_metadata.add(source["stat_energy_from"])
            validate_calls.append(
                functools.partial(
                    _async_validate_usage_stat,
                    hass,
                    statistics_metadata,
                    source["stat_energy_from"],
                    ENERGY_USAGE_DEVICE_CLASSES,
                    ENERGY_USAGE_UNITS,
                    ENERGY_UNIT_ERROR,
                    source_result,
                )
            )

        elif source["type"] == "battery":
            wanted_statistics_metadata.add(source["stat_energy_from"])
            validate_calls.append(
                functools.partial(
                    _async_validate_usage_stat,
                    hass,
                    statistics_metadata,
                    source["stat_energy_from"],
                    ENERGY_USAGE_DEVICE_CLASSES,
                    ENERGY_USAGE_UNITS,
                    ENERGY_UNIT_ERROR,
                    source_result,
                )
            )
            wanted_statistics_metadata.add(source["stat_energy_to"])
            validate_calls.append(
                functools.partial(
                    _async_validate_usage_stat,
                    hass,
                    statistics_metadata,
                    source["stat_energy_to"],
                    ENERGY_USAGE_DEVICE_CLASSES,
                    ENERGY_USAGE_UNITS,
                    ENERGY_UNIT_ERROR,
                    source_result,
                )
            )

    for device in manager.data["device_consumption"]:
        device_result = ValidationIssues()
        result.device_consumption.append(device_result)
        wanted_statistics_metadata.add(device["stat_consumption"])
        validate_calls.append(
            functools.partial(
                _async_validate_usage_stat,
                hass,
                statistics_metadata,
                device["stat_consumption"],
                ENERGY_USAGE_DEVICE_CLASSES,
                ENERGY_USAGE_UNITS,
                ENERGY_UNIT_ERROR,
                device_result,
            )
        )

    for device in manager.data.get("device_consumption_water", []):
        device_result = ValidationIssues()
        result.device_consumption_water.append(device_result)
        wanted_statistics_metadata.add(device["stat_consumption"])
        validate_calls.append(
            functools.partial(
                _async_validate_usage_stat,
                hass,
                statistics_metadata,
                device["stat_consumption"],
                WATER_USAGE_DEVICE_CLASSES,
                WATER_USAGE_UNITS,
                WATER_UNIT_ERROR,
                device_result,
            )
        )

    # Fetch the needed statistics metadata
    statistics_metadata.update(
        await recorder.get_instance(hass).async_add_executor_job(
            functools.partial(
                recorder.statistics.get_metadata,
                hass,
                statistic_ids=set(wanted_statistics_metadata),
            )
        )
    )

    # Execute all the validation checks
    for call in validate_calls:
        call()

    return result
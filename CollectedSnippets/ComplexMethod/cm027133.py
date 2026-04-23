def _async_import_statistics(
    hass: HomeAssistant,
    metadata: StatisticMetaData,
    statistics: Iterable[StatisticData],
) -> None:
    """Validate timestamps and insert an import_statistics job in the queue."""
    if "mean_type" not in metadata:
        metadata["mean_type"] = (  # type: ignore[unreachable]
            StatisticMeanType.ARITHMETIC
            if metadata.pop("has_mean", False)
            else StatisticMeanType.NONE
        )

    # If unit class is not set, we try to set it based on the unit of measurement
    # Note: This can't happen from the type checker's perspective, but we need
    # to guard against custom integrations that have not been updated to set
    # the unit_class.
    if "unit_class" not in metadata:
        unit = metadata["unit_of_measurement"]  # type: ignore[unreachable]
        if unit in STATISTIC_UNIT_TO_UNIT_CONVERTER:
            metadata["unit_class"] = STATISTIC_UNIT_TO_UNIT_CONVERTER[unit].UNIT_CLASS
        else:
            metadata["unit_class"] = None

    if (unit_class := metadata["unit_class"]) is not None:
        if (converter := UNIT_CLASS_TO_UNIT_CONVERTER.get(unit_class)) is None:
            raise HomeAssistantError(f"Unsupported unit_class: '{unit_class}'")

        if metadata["unit_of_measurement"] not in converter.VALID_UNITS:
            raise HomeAssistantError(
                f"Unsupported unit_of_measurement '{metadata['unit_of_measurement']}' "
                f"for unit_class '{unit_class}'"
            )

    for statistic in statistics:
        start = statistic["start"]
        if start.tzinfo is None or start.tzinfo.utcoffset(start) is None:
            raise HomeAssistantError(
                "Naive timestamp: no or invalid timezone info provided"
            )
        if start.minute != 0 or start.second != 0 or start.microsecond != 0:
            raise HomeAssistantError(
                "Invalid timestamp: timestamps must be from the top of the hour (minutes and seconds = 0)"
            )

        statistic["start"] = dt_util.as_utc(start)

        if "last_reset" in statistic and statistic["last_reset"] is not None:
            last_reset = statistic["last_reset"]
            if (
                last_reset.tzinfo is None
                or last_reset.tzinfo.utcoffset(last_reset) is None
            ):
                raise HomeAssistantError("Naive timestamp")
            statistic["last_reset"] = dt_util.as_utc(last_reset)

    # Insert job in recorder's queue
    get_instance(hass).async_import_statistics(metadata, statistics, Statistics)
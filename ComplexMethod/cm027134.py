def async_import_statistics(
    hass: HomeAssistant,
    metadata: StatisticMetaData,
    statistics: Iterable[StatisticData],
    *,
    _called_from_ws_api: bool = False,
) -> None:
    """Import hourly statistics from an internal source.

    This inserts an import_statistics job in the recorder's queue.
    """
    if not valid_entity_id(metadata["statistic_id"]):
        raise HomeAssistantError("Invalid statistic_id")

    # The source must not be empty and must be aligned with the statistic_id
    if not metadata["source"] or metadata["source"] != DOMAIN:
        raise HomeAssistantError("Invalid source")

    if "mean_type" not in metadata and not _called_from_ws_api:  # type: ignore[unreachable]
        report_usage(  # type: ignore[unreachable]
            "doesn't specify mean_type when calling async_import_statistics",
            breaks_in_ha_version="2026.11",
            exclude_integrations={DOMAIN},
        )
    if "unit_class" not in metadata and not _called_from_ws_api:  # type: ignore[unreachable]
        report_usage(  # type: ignore[unreachable]
            "doesn't specify unit_class when calling async_import_statistics",
            breaks_in_ha_version="2026.11",
            exclude_integrations={DOMAIN},
        )

    _async_import_statistics(hass, metadata, statistics)
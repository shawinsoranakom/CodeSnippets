def async_update_statistics_metadata(
    hass: HomeAssistant,
    statistic_id: str,
    *,
    new_statistic_id: str | UndefinedType = UNDEFINED,
    new_unit_class: str | None | UndefinedType = UNDEFINED,
    new_unit_of_measurement: str | None | UndefinedType = UNDEFINED,
    on_done: Callable[[], None] | None = None,
    _called_from_ws_api: bool = False,
) -> None:
    """Update statistics metadata for a statistic_id."""
    if new_unit_of_measurement is not UNDEFINED and new_unit_class is UNDEFINED:
        if not _called_from_ws_api:
            report_usage(
                (
                    "doesn't specify unit_class when calling "
                    "async_update_statistics_metadata"
                ),
                breaks_in_ha_version="2026.11",
                exclude_integrations={DOMAIN},
            )

        unit = new_unit_of_measurement
        if unit in STATISTIC_UNIT_TO_UNIT_CONVERTER:
            new_unit_class = STATISTIC_UNIT_TO_UNIT_CONVERTER[unit].UNIT_CLASS
        else:
            new_unit_class = None

    if TYPE_CHECKING:
        # After the above check, new_unit_class is guaranteed to not be UNDEFINED
        assert new_unit_class is not UNDEFINED

    if new_unit_of_measurement is not UNDEFINED and new_unit_class is not None:
        if (converter := UNIT_CLASS_TO_UNIT_CONVERTER.get(new_unit_class)) is None:
            raise HomeAssistantError(f"Unsupported unit_class: '{new_unit_class}'")

        if new_unit_of_measurement not in converter.VALID_UNITS:
            raise HomeAssistantError(
                f"Unsupported unit_of_measurement '{new_unit_of_measurement}' "
                f"for unit_class '{new_unit_class}'"
            )

    get_instance(hass).async_update_statistics_metadata(
        statistic_id,
        new_statistic_id=new_statistic_id,
        new_unit_class=new_unit_class,
        new_unit_of_measurement=new_unit_of_measurement,
        on_done=on_done,
    )
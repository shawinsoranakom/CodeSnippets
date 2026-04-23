def _async_validate_stat_common(
    hass: HomeAssistant,
    metadata: dict[str, tuple[int, recorder.models.StatisticMetaData]],
    stat_id: str,
    allowed_device_classes: Sequence[str],
    allowed_units: Mapping[str, Sequence[str]],
    unit_error: str,
    issues: ValidationIssues,
    check_negative: bool = False,
) -> str | None:
    """Validate common aspects of a statistic.

    Returns the entity_id if validation succeeds, None otherwise.
    """
    if stat_id not in metadata:
        issues.add_issue(hass, "statistics_not_defined", stat_id)

    has_entity_source = valid_entity_id(stat_id)

    if not has_entity_source:
        return None

    entity_id = stat_id

    if not recorder.is_entity_recorded(hass, entity_id):
        issues.add_issue(hass, "recorder_untracked", entity_id)
        return None

    if (state := hass.states.get(entity_id)) is None:
        issues.add_issue(hass, "entity_not_defined", entity_id)
        return None

    if state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
        issues.add_issue(hass, "entity_unavailable", entity_id, state.state)
        return None

    try:
        current_value: float | None = float(state.state)
    except ValueError:
        issues.add_issue(hass, "entity_state_non_numeric", entity_id, state.state)
        return None

    if check_negative and current_value is not None and current_value < 0:
        issues.add_issue(hass, "entity_negative_state", entity_id, current_value)

    device_class = state.attributes.get(ATTR_DEVICE_CLASS)
    if device_class not in allowed_device_classes:
        issues.add_issue(
            hass, "entity_unexpected_device_class", entity_id, device_class
        )
    else:
        unit = state.attributes.get("unit_of_measurement")

        if device_class and unit not in allowed_units.get(device_class, []):
            issues.add_issue(hass, unit_error, entity_id, unit)

    return entity_id
def _async_validate_cost_stat(
    hass: HomeAssistant,
    metadata: dict[str, tuple[int, recorder.models.StatisticMetaData]],
    stat_id: str,
    issues: ValidationIssues,
) -> None:
    """Validate that the cost stat is correct."""
    if stat_id not in metadata:
        issues.add_issue(hass, "statistics_not_defined", stat_id)

    has_entity = valid_entity_id(stat_id)

    if not has_entity:
        return

    if not recorder.is_entity_recorded(hass, stat_id):
        issues.add_issue(hass, "recorder_untracked", stat_id)

    if (state := hass.states.get(stat_id)) is None:
        issues.add_issue(hass, "entity_not_defined", stat_id)
        return

    state_class = state.attributes.get("state_class")

    supported_state_classes = [
        sensor.SensorStateClass.MEASUREMENT,
        sensor.SensorStateClass.TOTAL,
        sensor.SensorStateClass.TOTAL_INCREASING,
    ]
    if state_class not in supported_state_classes:
        issues.add_issue(hass, "entity_unexpected_state_class", stat_id, state_class)

    if (
        state_class == sensor.SensorStateClass.MEASUREMENT
        and sensor.ATTR_LAST_RESET not in state.attributes
    ):
        issues.add_issue(hass, "entity_state_class_measurement_no_last_reset", stat_id)
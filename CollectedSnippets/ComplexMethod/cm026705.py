async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, Any] | None,
) -> RepairsFlow:
    """Create flow."""
    entry = None
    if data and (entry_id := data.get("entry_id")):
        entry_id = cast(str, entry_id)
        entry = hass.config_entries.async_get_entry(entry_id)

    if data and (holiday := data.get("named_holiday")) and entry:
        # Bad named holiday in configuration
        return HolidayFixFlow(entry, data.get("country"), holiday)

    if data and entry:
        # Country or province does not exist
        return CountryFixFlow(entry, data.get("country"))

    return ConfirmRepairFlow()
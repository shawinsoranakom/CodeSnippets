async def test_options(hass: HomeAssistant) -> None:
    """Test updating options."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Islamic Prayer Times",
        data=MOCK_CONFIG,
        options={CONF_CALC_METHOD: "isna"},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_CALC_METHOD: "makkah",
            CONF_LAT_ADJ_METHOD: "one_seventh",
            CONF_SCHOOL: "hanafi",
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_CALC_METHOD] == "makkah"
    assert result["data"][CONF_LAT_ADJ_METHOD] == "one_seventh"
    assert result["data"][CONF_MIDNIGHT_MODE] == "standard"
    assert result["data"][CONF_SCHOOL] == "hanafi"
async def test_user_setup_removes_ignored_entry(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    ignored_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=DKEY_DISCOVERY_INFO.address,
        source=SOURCE_IGNORE,
    )
    ignored_entry.add_to_hass(hass)
    assert hass.config_entries.async_entries(DOMAIN) == [ignored_entry]

    with patch(
        "homeassistant.components.dormakaba_dkey.config_flow.async_discovered_service_info",
        return_value=[NOT_DKEY_DISCOVERY_INFO, DKEY_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_ADDRESS: DKEY_DISCOVERY_INFO.address,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "associate"
    assert result["errors"] is None

    await _test_common_success(hass, result)

    # Check the ignored entry is removed
    assert ignored_entry not in hass.config_entries.async_entries(DOMAIN)
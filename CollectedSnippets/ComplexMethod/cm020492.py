async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mocked_dev: Device,
    fixture_file: str,
    sysinfo_vars: list[str],
    expected_oui: str | None,
) -> None:
    """Test diagnostics for config entry."""
    diagnostics_data = json.loads(await async_load_fixture(hass, fixture_file, DOMAIN))

    mocked_dev.internal_state = diagnostics_data["device_last_response"]

    config_entry = await initialize_config_entry_for_device(hass, mocked_dev)
    result = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)

    assert isinstance(result, dict)
    assert "device_last_response" in result

    # There must be some redactions in place, so the raw data must not match
    assert result["device_last_response"] != diagnostics_data["device_last_response"]

    last_response = result["device_last_response"]

    # We should always have sysinfo available
    assert "system" in last_response
    assert "get_sysinfo" in last_response["system"]

    sysinfo = last_response["system"]["get_sysinfo"]
    for var in sysinfo_vars:
        assert sysinfo[var] == "**REDACTED**"

    assert result["oui"] == expected_oui
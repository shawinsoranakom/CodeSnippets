async def test_ssdp(
    hass: HomeAssistant,
    fritz: Mock,
    test_data: SsdpServiceInfo,
    expected_result: str,
) -> None:
    """Test starting a flow from discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=test_data
    )
    assert result["type"] == expected_result

    if expected_result is FlowResultType.ABORT:
        return

    assert result["step_id"] == "confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "fake_pass", CONF_USERNAME: "fake_user"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == CONF_FAKE_NAME
    assert result["data"][CONF_HOST] == urlparse(test_data.ssdp_location).hostname
    assert result["data"][CONF_PASSWORD] == "fake_pass"
    assert result["data"][CONF_USERNAME] == "fake_user"
    assert result["result"].unique_id == "only-a-test"
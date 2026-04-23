async def test_ssdp(hass: HomeAssistant) -> None:
    """Test starting a flow from discovery."""
    # confirm to add the entry
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_SSDP}, data=MOCK_SSDP_DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # entry was added
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "UE55H6400"
    assert result["data"][CONF_HOST] == "10.10.12.34"
    assert result["data"][CONF_MANUFACTURER] == "Samsung Electronics"
    assert result["data"][CONF_MODEL] == "UE55H6400"
    assert result["data"][CONF_PORT] == 55000
    assert result["result"].unique_id == "068e7781-006e-1000-bbbf-84a4668d8423"
async def test_zeroconf_discovery(
    hass: HomeAssistant,
    mock_powerfox_local_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "zeroconf_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == f"Poweropti ({MOCK_DEVICE_ID[-5:]})"
    assert result.get("data") == {
        CONF_HOST: MOCK_HOST,
        CONF_API_KEY: MOCK_API_KEY,
    }
    assert result["result"].unique_id == MOCK_DEVICE_ID
    assert len(mock_setup_entry.mock_calls) == 1
async def test_zeroconf_discovery(
    hass: HomeAssistant,
    mock_powerfox_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert not result.get("errors")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == "test@powerfox.test"
    assert result.get("data") == {
        CONF_EMAIL: "test@powerfox.test",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_powerfox_client.all_devices.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
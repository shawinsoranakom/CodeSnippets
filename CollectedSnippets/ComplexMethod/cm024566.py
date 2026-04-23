async def test_user_flow(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the full user initiated config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "Test device"
    assert result2.get("data") == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
        CONF_SSL: False,
        CONF_VERIFY_SSL: False,
    }
    assert "result" in result2
    assert result2["result"].unique_id == "12345"

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1
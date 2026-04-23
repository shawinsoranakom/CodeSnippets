async def test_errors(
    hass: HomeAssistant,
    mock_fully_kiosk_config_flow: MagicMock,
    mock_setup_entry: AsyncMock,
    side_effect: Exception,
    reason: str,
) -> None:
    """Test errors raised during flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    flow_id = result["flow_id"]

    mock_fully_kiosk_config_flow.getDeviceInfo.side_effect = side_effect
    result2 = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: False,
            CONF_VERIFY_SSL: False,
        },
    )

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("step_id") == "user"
    assert result2.get("errors") == {"base": reason}

    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 0

    mock_fully_kiosk_config_flow.getDeviceInfo.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        flow_id,
        user_input={
            CONF_HOST: "1.1.1.1",
            CONF_PASSWORD: "test-password",
            CONF_SSL: True,
            CONF_VERIFY_SSL: False,
        },
    )

    assert result3.get("type") is FlowResultType.CREATE_ENTRY
    assert result3.get("title") == "Test device"
    assert result3.get("data") == {
        CONF_HOST: "1.1.1.1",
        CONF_PASSWORD: "test-password",
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
        CONF_SSL: True,
        CONF_VERIFY_SSL: False,
    }
    assert "result" in result3
    assert result3["result"].unique_id == "12345"

    assert len(mock_fully_kiosk_config_flow.getDeviceInfo.mock_calls) == 2
    assert len(mock_setup_entry.mock_calls) == 1
async def test_form_duplicate_entries(
    hass: HomeAssistant,
    mock_pyotgw: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test duplicate device or id errors."""
    flow1 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    flow3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    result1 = await hass.config_entries.flow.async_configure(
        flow1["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    assert result1["type"] is FlowResultType.CREATE_ENTRY

    result2 = await hass.config_entries.flow.async_configure(
        flow2["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB1"}
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "id_exists"}

    result3 = await hass.config_entries.flow.async_configure(
        flow3["flow_id"], {CONF_NAME: "Test Entry 2", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "already_configured"}

    assert mock_pyotgw.return_value.connect.await_count == 1
    assert mock_pyotgw.return_value.disconnect.await_count == 1
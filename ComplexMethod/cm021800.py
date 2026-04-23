async def test_form_user(
    hass: HomeAssistant,
    mock_pyotgw: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_NAME: "Test Entry 1", CONF_DEVICE: "/dev/ttyUSB0"}
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Entry 1"
    assert result2["data"] == {
        CONF_NAME: "Test Entry 1",
        CONF_DEVICE: "/dev/ttyUSB0",
        CONF_ID: "test_entry_1",
    }
    assert mock_pyotgw.return_value.connect.await_count == 1
    assert mock_pyotgw.return_value.disconnect.await_count == 1
async def test_pin_format_serial_bridge(
    hass: HomeAssistant,
    mock_serial_bridge: AsyncMock,
    mock_serial_bridge_config_entry: MockConfigEntry,
) -> None:
    """Test PIN is valid format."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BAD_PIN,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_pin"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: BRIDGE_HOST,
            CONF_PORT: BRIDGE_PORT,
            CONF_PIN: BRIDGE_PIN,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_HOST: BRIDGE_HOST,
        CONF_PORT: BRIDGE_PORT,
        CONF_PIN: BRIDGE_PIN,
        CONF_TYPE: BRIDGE,
    }
    assert not result["result"].unique_id
    await hass.async_block_till_done()
async def test_modbus_device_error(
    hass: HomeAssistant,
    mock_pyiskra_modbus,
    s_effect,
    reason,
) -> None:
    """Test device error with Modbus TCP protocol."""
    mock_pyiskra_modbus.side_effect = s_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "modbus_tcp"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "modbus_tcp"
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    # Test if error returned
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "modbus_tcp"
    assert result["errors"] == {"base": reason}

    # Remove side effect
    mock_pyiskra_modbus.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PORT: MODBUS_PORT,
            CONF_ADDRESS: MODBUS_ADDRESS,
        },
    )

    # Test successful Modbus TCP configuration
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == PQ_MODEL
    assert result["data"] == {
        CONF_HOST: HOST,
        CONF_PROTOCOL: "modbus_tcp",
        CONF_PORT: MODBUS_PORT,
        CONF_ADDRESS: MODBUS_ADDRESS,
    }
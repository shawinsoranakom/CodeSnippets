async def test_user_modbus(hass: HomeAssistant, mock_pyiskra_modbus) -> None:
    """Test the user flow with Modbus TCP protocol."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    # Test if user form is provided
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "modbus_tcp"},
    )

    # Test if propmpted to enter port and address
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "modbus_tcp"

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
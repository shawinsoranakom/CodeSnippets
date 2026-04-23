async def test_rest_device_error(
    hass: HomeAssistant,
    mock_pyiskra_rest,
    s_effect,
    reason,
) -> None:
    """Test device error with Modbus TCP protocol."""
    mock_pyiskra_rest.side_effect = s_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    # Test if error returned
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": reason}

    # Remove side effect
    mock_pyiskra_rest.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"},
    )

    # Test successful Rest API configuration
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == SG_MODEL
    assert result["data"] == {CONF_HOST: HOST, CONF_PROTOCOL: "rest_api"}
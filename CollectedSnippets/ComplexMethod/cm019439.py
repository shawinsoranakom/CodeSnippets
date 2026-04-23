async def test_create_entry(
    hass: HomeAssistant, config, connect_errors, connect_mock, pro, setup_airvisual_pro
) -> None:
    """Test creating an entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test errors that can arise when connecting to a Pro:
    with patch.object(pro, "async_connect", connect_mock):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=config
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == connect_errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=config
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "192.168.1.101"
    assert result["data"] == {
        CONF_IP_ADDRESS: "192.168.1.101",
        CONF_PASSWORD: "password123",
    }
async def test_user_selection(hass: HomeAssistant) -> None:
    """Test we can select a device."""

    await hass.async_block_till_done(wait_background_tasks=True)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # mock connection error
    with patch(
        "homeassistant.components.husqvarna_automower_ble.config_flow.HusqvarnaAutomowerBleConfigFlow.probe_mower",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
                CONF_PIN: "1234",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
            CONF_PIN: "1234",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Husqvarna Automower"
    assert result["result"].unique_id == "00000000-0000-0000-0000-000000000001"

    assert result["data"] == {
        CONF_ADDRESS: "00000000-0000-0000-0000-000000000001",
        CONF_CLIENT_ID: 1197489078,
        CONF_PIN: "1234",
    }
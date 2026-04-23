async def test_form_manual_entry(hass: HomeAssistant) -> None:
    """Test we get the form."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        return_value=[
            {
                SL_GATEWAY_IP: "1.1.1.1",
                SL_GATEWAY_PORT: 80,
                SL_GATEWAY_TYPE: 12,
                SL_GATEWAY_SUBTYPE: 2,
                SL_GATEWAY_NAME: "Pentair: 01-01-01",
            },
        ],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "gateway_select"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={GATEWAY_SELECT_KEY: GATEWAY_MANUAL_ENTRY}
    )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {}
    assert result2["step_id"] == "gateway_entry"

    with (
        patch(
            "homeassistant.components.screenlogic.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.screenlogic.config_flow.login.async_get_mac_address",
            return_value="00-C0-33-01-01-01",
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_IP_ADDRESS: "1.1.1.1",
                CONF_PORT: 80,
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Pentair: 01-01-01"
    assert result3["data"] == {
        CONF_IP_ADDRESS: "1.1.1.1",
        CONF_PORT: 80,
    }
    assert len(mock_setup_entry.mock_calls) == 1
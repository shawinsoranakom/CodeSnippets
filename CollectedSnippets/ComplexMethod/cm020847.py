async def test_flow_discovery(hass: HomeAssistant) -> None:
    """Test the flow works with basic discovery."""

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

    with patch(
        "homeassistant.components.screenlogic.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={GATEWAY_SELECT_KEY: "00:c0:33:01:01:01"}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Pentair: 01-01-01"
    assert result2["data"] == {
        CONF_IP_ADDRESS: "1.1.1.1",
        CONF_PORT: 80,
    }
    assert len(mock_setup_entry.mock_calls) == 1
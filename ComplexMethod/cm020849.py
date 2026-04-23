async def test_flow_discover_error(hass: HomeAssistant) -> None:
    """Test when discovery errors."""

    with patch(
        "homeassistant.components.screenlogic.config_flow.discovery.async_discover",
        side_effect=ScreenLogicError("Fake error"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "gateway_entry"

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
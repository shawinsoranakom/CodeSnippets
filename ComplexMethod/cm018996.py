async def test_form(hass: HomeAssistant, info: dict[str, Any]) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.devolo_home_network.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_IP_ADDRESS: IP, CONF_PASSWORD: ""},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["result"].unique_id == info[SERIAL_NUMBER]
    assert result2["title"] == info[TITLE]
    assert result2["data"] == {
        CONF_IP_ADDRESS: IP,
        CONF_PASSWORD: "",
    }
    assert len(mock_setup_entry.mock_calls) == 1
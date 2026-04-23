async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""

    with patch("homeassistant.components.epson.Projector.get_power", return_value="01"):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == config_entries.SOURCE_USER
    with (
        patch(
            "homeassistant.components.epson.Projector.get_power",
            return_value="01",
        ),
        patch(
            "homeassistant.components.epson.Projector.get_serial_number",
            return_value="12345",
        ),
        patch(
            "homeassistant.components.epson.async_setup_entry",
            return_value=True,
        ),
        patch(
            "homeassistant.components.epson.Projector.close",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "1.1.1.1", CONF_NAME: "test-epson"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "test-epson"
    assert result2["data"] == {CONF_CONNECTION_TYPE: HTTP, CONF_HOST: "1.1.1.1"}
    assert len(mock_setup_entry.mock_calls) == 1
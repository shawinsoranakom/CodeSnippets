async def test_user_setup_wocurtain(hass: HomeAssistant) -> None:
    """Test the user initiated form with password and valid mac."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.switchbot.config_flow.async_discovered_service_info",
        return_value=[WOCURTAIN_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"next_step_id": "select_device"},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["errors"] is None

    with patch_async_setup_entry() as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Curtain EEFF"
    assert result["data"] == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_SENSOR_TYPE: "curtain",
    }

    assert len(mock_setup_entry.mock_calls) == 1
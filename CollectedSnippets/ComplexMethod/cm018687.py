async def test_no_link(hass: HomeAssistant) -> None:
    """Test the user initiated form with invalid response."""

    with (
        patch_microbot_api(),
        patch(
            "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
            return_value=[SERVICE_INFO],
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["errors"] == {}

    with patch_microbot_api():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "link"
    with (
        patch(
            "homeassistant.components.keymitt_ble.config_flow.MicroBotApiClient",
            MockMicroBotApiClientFail,
        ),
        patch_async_setup_entry() as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "link"
    assert result3["errors"] == {"base": "linking"}

    assert len(mock_setup_entry.mock_calls) == 0
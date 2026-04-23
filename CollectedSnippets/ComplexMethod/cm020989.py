async def test_reconfigure_flow_logout_failed(
    hass: HomeAssistant,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
    side_effect: list,
    expected_error: str,
    expected_description_placeholders: dict[str, str],
) -> None:
    """Test reconfigure flow for with change in API endpoint and logout failed."""

    mock_broadcast_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_broadcast_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await mock_broadcast_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.telegram_bot.bot.Bot.log_out",
        AsyncMock(side_effect=side_effect),
    ):
        # first logout attempt fails

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PLATFORM: PLATFORM_BROADCAST,
                SECTION_ADVANCED_SETTINGS: {
                    CONF_API_ENDPOINT: "http://mock1",
                },
            },
        )
        await hass.async_block_till_done()

        assert result["step_id"] == "reconfigure"
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": expected_error}
        assert result["description_placeholders"] == expected_description_placeholders

        # second logout attempt success

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_PLATFORM: PLATFORM_BROADCAST,
                SECTION_ADVANCED_SETTINGS: {
                    CONF_API_ENDPOINT: "http://mock2",
                },
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_broadcast_config_entry.data[CONF_API_ENDPOINT] == "http://mock2"
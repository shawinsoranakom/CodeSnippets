async def test_addon_discovery_info_error(
    hass: HomeAssistant,
    addon_info: AsyncMock,
    get_addon_discovery_info: AsyncMock,
) -> None:
    """Test we perform an auto config flow with a supervised install.

    Case: The Mosquitto add-on start on a discovery error.
    """
    get_addon_discovery_info.side_effect = AddonError

    result = await hass.config_entries.flow.async_init(
        "mqtt", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["addon", "broker"]
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "addon"},
    )
    # Addon will retry
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "start_addon"
    assert result["step_id"] == "start_addon"
    await hass.async_block_till_done()
    await hass.async_block_till_done(wait_background_tasks=True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "start_addon"},
    )

    # add-on start-up failed
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_start_failed"
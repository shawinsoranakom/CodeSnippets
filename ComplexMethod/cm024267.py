async def test_addon_not_installed_failures(
    hass: HomeAssistant,
    install_addon: AsyncMock,
) -> None:
    """Test we perform an auto config flow with a supervised install.

    Case: The Mosquitto add-on install fails.
    """
    install_addon.side_effect = SupervisorError()

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
    # add-on not installed, so we wait for install
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "install_addon"
    assert result["step_id"] == "install_addon"
    await hass.async_block_till_done()
    await hass.async_block_till_done(wait_background_tasks=True)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "install_addon"},
    )

    # add-on install failed
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "addon_install_failed"
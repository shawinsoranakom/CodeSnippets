async def test_addon_flow_with_supervisor_addon_not_installed(
    hass: HomeAssistant,
    mock_try_connection_success: MagicMock,
    mock_finish_setup: MagicMock,
) -> None:
    """Test we perform an auto config flow with a supervised install.

    Case: The Mosquitto add-on is not yet installed nor running.
    """
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

    # add-on installed but not started, so we wait for start-up
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["progress_action"] == "start_addon"
    assert result["step_id"] == "start_addon"
    await hass.async_block_till_done()
    await hass.async_block_till_done(wait_background_tasks=True)
    mock_try_connection_success.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "start_addon"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data == {
        "broker": "core-mosquitto",
        "port": 1883,
        "username": "mock-user",
        "password": "mock-pass",
        "discovery": True,
    }
    # Check we tried the connection
    assert len(mock_try_connection_success.mock_calls)
    # Check config entry got setup
    assert len(mock_finish_setup.mock_calls) == 1
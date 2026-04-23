async def test_addon_flow_with_supervisor_addon_running(
    hass: HomeAssistant,
    mock_try_connection_success: MagicMock,
    mock_finish_setup: MagicMock,
) -> None:
    """Test we perform an auto config flow with a supervised install.

    Case: The Mosquitto add-on is already installed, and running.
    """
    # show menu
    result = await hass.config_entries.flow.async_init(
        "mqtt", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["addon", "broker"]
    assert result["step_id"] == "user"

    # select install via add-on
    mock_try_connection_success.reset_mock()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "addon"},
    )
    await hass.async_block_till_done(wait_background_tasks=True)
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
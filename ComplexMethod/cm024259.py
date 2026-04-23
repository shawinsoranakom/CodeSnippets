async def test_user_connection_works_with_supervisor(
    hass: HomeAssistant,
    mock_try_connection: MagicMock,
    mock_finish_setup: MagicMock,
) -> None:
    """Test we can finish a config flow with a supervised install."""
    mock_try_connection.return_value = True

    result = await hass.config_entries.flow.async_init(
        "mqtt", context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["addon", "broker"]
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "broker"},
    )

    # Assert a manual setup flow
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"broker": "127.0.0.1"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data == {
        "broker": "127.0.0.1",
        "port": 1883,
    }
    # Check we tried the connection
    assert len(mock_try_connection.mock_calls) == 1
    # Check config entry got setup
    assert len(mock_finish_setup.mock_calls) == 1
    await hass.async_block_till_done(wait_background_tasks=True)
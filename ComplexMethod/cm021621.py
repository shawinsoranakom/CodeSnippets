async def test_full_manual(
    hass: HomeAssistant,
    mock_lametric: MagicMock,
) -> None:
    """Check a full flow manual entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "choice_enter_manual_or_fetch_cloud"
    assert result["menu_options"] == ["pick_implementation", "manual_entry"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "manual_entry"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_entry"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1", CONF_API_KEY: "mock-api-key"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]

    assert config_entry.title == "Frenck's LaMetric"
    assert config_entry.unique_id == "SA110405124500W00BS9"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_API_KEY: "mock-api-key",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }
    assert not config_entry.options

    assert len(mock_lametric.device.mock_calls) == 1
    assert len(mock_lametric.notify.mock_calls) == 1

    notification: Notification = mock_lametric.notify.mock_calls[0][2]["notification"]
    assert notification.model.sound == Sound(sound=NotificationSound.WIN)
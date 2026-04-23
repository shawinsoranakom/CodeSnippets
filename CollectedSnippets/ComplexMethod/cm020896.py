async def test_bad_code_attempt_event_fired(hass: HomeAssistant) -> None:
    """Test that manual_alarm_bad_code_attempt event is fired on bad code."""

    entity_id = "alarm_control_panel.test_alarm"
    config = {
        ALARM_DOMAIN: {
            "platform": "manual",
            "name": "Test Alarm",
            "code": "1234",
            "delay_time": 0,
            "arming_time": 0,
            "trigger_time": 0,
        }
    }
    assert await async_setup_component(hass, ALARM_DOMAIN, config)
    await hass.async_block_till_done()

    alarm_entity = hass.states.get(entity_id)
    assert alarm_entity is not None

    await hass.services.async_call(
        ALARM_DOMAIN,
        "alarm_arm_away",
        {"entity_id": entity_id, "code": "1234"},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == AlarmControlPanelState.ARMED_AWAY

    bad_code = "0000"

    mock_user_id = "test_user_id_123"
    test_context = Context(user_id=mock_user_id)

    events = []

    @callback
    def event_listener(event):
        events.append(event.data)

    hass.bus.async_listen("manual_alarm_bad_code_attempt", event_listener)

    await hass.services.async_call(
        ALARM_DOMAIN,
        "alarm_disarm",
        {"entity_id": entity_id, "code": "1234"},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert len(events) == 0

    with patch("homeassistant.auth.AuthManager.async_get_user") as mock_get_user:
        mock_user = MagicMock(spec=User)
        mock_user.id = mock_user_id
        mock_get_user.return_value = mock_user

        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                ALARM_DOMAIN,
                "alarm_disarm",
                {"entity_id": entity_id, "code": bad_code},
                blocking=True,
                context=test_context,
            )

    await hass.async_block_till_done()

    assert len(events) == 1
    assert events[0].get("entity_id") == entity_id
    assert events[0].get("target_state") == AlarmControlPanelState.DISARMED
    assert events[0].get("user_id") == mock_user_id
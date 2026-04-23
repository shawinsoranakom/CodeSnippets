async def test_availability(
    hass: HomeAssistant,
    client,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that availability status changes are set and logged correctly."""
    await setup_webostv(hass)

    # Initially available
    assert hass.states.get(ENTITY_ID).state == MediaPlayerState.ON

    # Make the entity go offline - should log unavailable message
    client.connect.side_effect = TimeoutError
    client.is_connected.return_value = False
    await mock_scan_interval(hass, freezer)

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    unavailable_log = f"LG webOS TV entity {ENTITY_ID} is unavailable"
    assert unavailable_log in caplog.text

    # Clear logs and update the offline entity again - should NOT log again
    caplog.clear()
    await mock_scan_interval(hass, freezer)

    assert unavailable_log not in caplog.text

    # Bring the entity back online - should log back online message
    client.connect.side_effect = None
    await mock_scan_interval(hass, freezer)

    assert hass.states.get(ENTITY_ID).state == MediaPlayerState.ON
    available_log = f"LG webOS TV entity {ENTITY_ID} is back online"
    assert available_log in caplog.text

    # Clear logs and make update again - should NOT log again
    caplog.clear()
    await mock_scan_interval(hass, freezer)

    assert hass.states.get(ENTITY_ID).state == MediaPlayerState.ON
    assert available_log not in caplog.text

    # Test offline again to ensure the flag resets properly
    client.connect.side_effect = TimeoutError
    await mock_scan_interval(hass, freezer)

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    assert unavailable_log in caplog.text

    # Test entity that supports turn on are considered available
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "webostv.turn_on",
                        "entity_id": ENTITY_ID,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": ENTITY_ID,
                            "id": "{{ trigger.id }}",
                        },
                    },
                },
            ],
        },
    )

    await mock_scan_interval(hass, freezer)

    assert hass.states.get(ENTITY_ID).state == MediaPlayerState.ON
    available_log = f"LG webOS TV entity {ENTITY_ID} is back online"
    assert available_log in caplog.text
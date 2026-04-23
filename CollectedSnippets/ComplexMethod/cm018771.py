async def test_intent_script_action_validation(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test action validation in intent scripts.

    This tests that async_validate_actions_config is called during setup,
    which resolves entity registry IDs to entity IDs in conditions.
    Without async_validate_actions_config, the entity registry ID would not
    be resolved and the condition would fail.
    """
    calls = async_mock_service(hass, "test", "service")

    entry = entity_registry.async_get_or_create(
        "binary_sensor", "test", "1234", suggested_object_id="test_sensor"
    )
    assert entry.entity_id == "binary_sensor.test_sensor"

    # Use a non-existent entity registry ID to trigger validation error
    non_existent_registry_id = "abcd1234abcd1234abcd1234abcd1234"

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "ChooseWithRegistryIdIntent": {
                    "action": [
                        {
                            "choose": [
                                {
                                    "conditions": [
                                        {
                                            "condition": "state",
                                            # Use entity registry ID instead of entity_id
                                            # This requires async_validate_actions_config
                                            # to resolve to the actual entity_id
                                            "entity_id": entry.id,
                                            "state": "on",
                                        }
                                    ],
                                    "sequence": [
                                        {
                                            "action": "test.service",
                                            "data": {"result": "sensor_on"},
                                        }
                                    ],
                                }
                            ],
                            "default": [
                                {
                                    "action": "test.service",
                                    "data": {"result": "sensor_off"},
                                }
                            ],
                        }
                    ],
                    "speech": {"text": "Done"},
                },
                # This intent has an invalid entity registry ID and should fail validation
                "InvalidIntent": {
                    "action": [
                        {
                            "choose": [
                                {
                                    "conditions": [
                                        {
                                            "condition": "state",
                                            "entity_id": non_existent_registry_id,
                                            "state": "on",
                                        }
                                    ],
                                    "sequence": [
                                        {"action": "test.service"},
                                    ],
                                }
                            ],
                        }
                    ],
                    "speech": {"text": "Invalid"},
                },
            }
        },
    )

    # Verify that the invalid intent logged an error
    assert "Failed to validate actions for intent InvalidIntent" in caplog.text

    # The invalid intent should not be registered
    with pytest.raises(intent.UnknownIntent):
        await intent.async_handle(hass, "test", "InvalidIntent")

    # Test when condition is true (sensor is "on")
    hass.states.async_set("binary_sensor.test_sensor", "on")

    response = await intent.async_handle(hass, "test", "ChooseWithRegistryIdIntent")

    assert len(calls) == 1
    assert calls[0].data["result"] == "sensor_on"
    assert response.speech["plain"]["speech"] == "Done"

    calls.clear()

    # Test when condition is false (sensor is "off")
    hass.states.async_set("binary_sensor.test_sensor", "off")

    response = await intent.async_handle(hass, "test", "ChooseWithRegistryIdIntent")

    assert len(calls) == 1
    assert calls[0].data["result"] == "sensor_off"
    assert response.speech["plain"]["speech"] == "Done"
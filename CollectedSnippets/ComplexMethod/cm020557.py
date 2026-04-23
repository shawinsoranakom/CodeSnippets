async def test_preferences_storage_load(
    hass: HomeAssistant,
) -> None:
    """Test that AITaskPreferences are stored and loaded correctly."""
    preferences = AITaskPreferences(hass)
    await preferences.async_load()

    # Initial state should be None for entity IDs
    for key in AITaskPreferences.KEYS:
        assert getattr(preferences, key) is None, f"Initial {key} should be None"

    new_values = {key: f"ai_task.test_{key}" for key in AITaskPreferences.KEYS}

    preferences.async_set_preferences(**new_values)

    # Verify that current preferences object is updated
    for key, value in new_values.items():
        assert getattr(preferences, key) == value, (
            f"Current {key} should match set value"
        )

    await flush_store(preferences._store)

    # Create a new preferences instance to test loading from store
    new_preferences_instance = AITaskPreferences(hass)
    await new_preferences_instance.async_load()

    for key in AITaskPreferences.KEYS:
        assert getattr(preferences, key) == getattr(new_preferences_instance, key), (
            f"Loaded {key} should match saved value"
        )
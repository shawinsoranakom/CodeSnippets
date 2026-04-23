async def test_motion_light(hass: HomeAssistant) -> None:
    """Test motion light blueprint."""
    hass.states.async_set("binary_sensor.kitchen", "off")

    with patch_blueprint(
        "motion_light.yaml",
        BUILTIN_BLUEPRINT_FOLDER / "motion_light.yaml",
    ):
        assert await async_setup_component(
            hass,
            "automation",
            {
                "automation": {
                    "use_blueprint": {
                        "path": "motion_light.yaml",
                        "input": {
                            "light_target": {"entity_id": "light.kitchen"},
                            "motion_entity": "binary_sensor.kitchen",
                        },
                    }
                }
            },
        )

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    turn_off_calls = async_mock_service(hass, "light", "turn_off")

    # Turn on motion
    hass.states.async_set("binary_sensor.kitchen", "on")
    # Can't block till done because delay is active
    # So wait 10 event loop iterations to process script
    for _ in range(10):
        await asyncio.sleep(0)

    assert len(turn_on_calls) == 1

    # Test light doesn't turn off if motion stays
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=200))

    for _ in range(10):
        await asyncio.sleep(0)

    assert len(turn_off_calls) == 0

    # Test light turns off off 120s after last motion
    hass.states.async_set("binary_sensor.kitchen", "off")

    for _ in range(10):
        await asyncio.sleep(0)

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=120))
    await hass.async_block_till_done()

    assert len(turn_off_calls) == 1

    # Test restarting the script
    hass.states.async_set("binary_sensor.kitchen", "on")

    for _ in range(10):
        await asyncio.sleep(0)

    assert len(turn_on_calls) == 2
    assert len(turn_off_calls) == 1

    hass.states.async_set("binary_sensor.kitchen", "off")

    for _ in range(10):
        await asyncio.sleep(0)

    hass.states.async_set("binary_sensor.kitchen", "on")

    for _ in range(15):
        await asyncio.sleep(0)

    assert len(turn_on_calls) == 3
    assert len(turn_off_calls) == 1

    # Verify trigger works
    await hass.services.async_call(
        "automation",
        "trigger",
        {"entity_id": "automation.automation_0"},
    )
    for _ in range(25):
        await asyncio.sleep(0)
    assert len(turn_on_calls) == 4
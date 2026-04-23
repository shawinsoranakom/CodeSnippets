async def test_bridge_with_two_fans_one_removed(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test a bridge with two fans and one gets removed."""

    # Set up a basic fan that does not support oscillation
    accessories = await setup_accessories_from_file(
        hass, "home_assistant_bridge_fan.json"
    )
    await setup_test_accessories(hass, accessories)

    fan = entity_registry.async_get("fan.living_room_fan")
    assert fan.unique_id == "00:00:00:00:00:00_1256851357_8"

    fan_state = hass.states.get("fan.living_room_fan")
    assert (
        fan_state.attributes[ATTR_SUPPORTED_FEATURES]
        is FanEntityFeature.SET_SPEED
        | FanEntityFeature.DIRECTION
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    fan = entity_registry.async_get("fan.ceiling_fan")
    assert fan.unique_id == "00:00:00:00:00:00_766313939_8"

    fan_state = hass.states.get("fan.ceiling_fan")
    assert (
        fan_state.attributes[ATTR_SUPPORTED_FEATURES]
        is FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )

    # Now change the config to remove one of the fans
    accessories = await setup_accessories_from_file(
        hass, "home_assistant_bridge_fan_one_removed.json"
    )
    await device_config_changed(hass, accessories)

    # Verify the first fan is still there
    fan_state = hass.states.get("fan.living_room_fan")
    assert entity_registry.async_get("fan.living_room_fan") is not None
    assert (
        fan_state.attributes[ATTR_SUPPORTED_FEATURES]
        is FanEntityFeature.SET_SPEED
        | FanEntityFeature.DIRECTION
        | FanEntityFeature.OSCILLATE
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.TURN_ON
    )
    # The second fan should have been removed
    assert not hass.states.get("fan.ceiling_fan")
    assert not entity_registry.async_get("fan.ceiling_fan")
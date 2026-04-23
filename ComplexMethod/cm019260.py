async def test_default_state(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test binary_sensor group default state."""
    hass.states.async_set("binary_sensor.kitchen", "on")
    hass.states.async_set("binary_sensor.bedroom", "on")
    await async_setup_component(
        hass,
        BINARY_SENSOR_DOMAIN,
        {
            BINARY_SENSOR_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["binary_sensor.kitchen", "binary_sensor.bedroom"],
                "name": "Bedroom Group",
                "unique_id": "unique_identifier",
                "device_class": "presence",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("binary_sensor.bedroom_group")
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_ENTITY_ID) == [
        "binary_sensor.kitchen",
        "binary_sensor.bedroom",
    ]

    entry = entity_registry.async_get("binary_sensor.bedroom_group")
    assert entry
    assert entry.unique_id == "unique_identifier"
    assert entry.original_name == "Bedroom Group"
    assert entry.original_device_class == "presence"
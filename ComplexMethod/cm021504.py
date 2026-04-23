async def test_no_update_template_match_all(hass: HomeAssistant) -> None:
    """Test that we do not update sensors that match on all."""

    hass.set_state(CoreState.not_running)

    await setup.async_setup_component(
        hass,
        template.DOMAIN,
        {
            "template": [
                {
                    "binary_sensor": [
                        {"name": "all_state", "state": "{{ True }}"},
                        {
                            "name": "all_icon",
                            "state": "{{ states('sensor.test_state') }}",
                            "icon": "{{ 1 + 1 }}",
                        },
                        {
                            "name": "all_entity_picture",
                            "state": "{{ states('sensor.test_state') }}",
                            "picture": "{{ 1 + 1 }}",
                        },
                        {
                            "name": "all_attribute",
                            "state": "{{ states('sensor.test_state') }}",
                            "attributes": {"test_attribute": "{{ 1 + 1 }}"},
                        },
                    ]
                }
            ]
        },
    )
    await hass.async_block_till_done()
    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_ON)
    assert len(hass.states.async_all()) == 5

    assert hass.states.get("binary_sensor.all_state").state == STATE_UNKNOWN
    assert hass.states.get("binary_sensor.all_icon").state == STATE_UNKNOWN
    assert hass.states.get("binary_sensor.all_entity_picture").state == STATE_UNKNOWN
    assert hass.states.get("binary_sensor.all_attribute").state == STATE_UNKNOWN

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    await hass.async_block_till_done()

    assert hass.states.get("binary_sensor.all_state").state == STATE_ON
    assert hass.states.get("binary_sensor.all_icon").state == STATE_ON
    assert hass.states.get("binary_sensor.all_entity_picture").state == STATE_ON
    assert hass.states.get("binary_sensor.all_attribute").state == STATE_ON

    await async_trigger(hass, TEST_STATE_ENTITY_ID, STATE_OFF)

    assert hass.states.get("binary_sensor.all_state").state == STATE_ON
    # Will now process because we have one valid template
    assert hass.states.get("binary_sensor.all_icon").state == STATE_OFF
    assert hass.states.get("binary_sensor.all_entity_picture").state == STATE_OFF
    assert hass.states.get("binary_sensor.all_attribute").state == STATE_OFF

    await async_update_entity(hass, "binary_sensor.all_state")
    await async_update_entity(hass, "binary_sensor.all_icon")
    await async_update_entity(hass, "binary_sensor.all_entity_picture")
    await async_update_entity(hass, "binary_sensor.all_attribute")

    assert hass.states.get("binary_sensor.all_state").state == STATE_ON
    assert hass.states.get("binary_sensor.all_icon").state == STATE_OFF
    assert hass.states.get("binary_sensor.all_entity_picture").state == STATE_OFF
    assert hass.states.get("binary_sensor.all_attribute").state == STATE_OFF
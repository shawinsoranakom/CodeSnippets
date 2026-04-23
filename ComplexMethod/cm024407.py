async def test_if_fires_on_zone_enter_uuid(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for firing on zone enter when device is specified by entity registry id."""
    context = Context()

    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="entity"
    )
    assert entry.entity_id == "test.entity"

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "zone",
                    "entity_id": entry.id,
                    "zone": "zone.test",
                    "event": "enter",
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": (
                            "{{ trigger.platform }}"
                            " - {{ trigger.entity_id }}"
                            " - {{ trigger.from_state.state }}"
                            " - {{ trigger.to_state.state }}"
                            " - {{ trigger.zone.name }}"
                            " - {{ trigger.id }}"
                        )
                    },
                },
            }
        },
    )

    hass.states.async_set(
        "test.entity",
        "hello",
        {"latitude": 32.880586, "longitude": -117.237564},
        context=context,
    )
    await hass.async_block_till_done()

    assert len(service_calls) == 1
    assert service_calls[0].context.parent_id == context.id
    assert (
        service_calls[0].data["some"] == "zone - test.entity - hello - hello - test - 0"
    )

    # Set out of zone again so we can trigger call
    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.881011, "longitude": -117.234758}
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    assert len(service_calls) == 2

    hass.states.async_set(
        "test.entity", "hello", {"latitude": 32.880586, "longitude": -117.237564}
    )
    await hass.async_block_till_done()

    assert len(service_calls) == 2
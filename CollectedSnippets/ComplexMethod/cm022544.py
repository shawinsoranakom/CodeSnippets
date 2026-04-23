async def test_if_fires_on_entity_change_below_uuid(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
    below: int | str,
) -> None:
    """Test the firing with changed entity specified by registry entry id."""
    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="entity"
    )
    assert entry.entity_id == "test.entity"

    hass.states.async_set("test.entity", 11)
    await hass.async_block_till_done()

    context = Context()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": entry.id,
                    "below": below,
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {"id": "{{ trigger.id}}"},
                },
            }
        },
    )
    # 9 is below 10
    hass.states.async_set("test.entity", 9, context=context)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].context.parent_id == context.id

    # Set above 12 so the automation will fire again
    hass.states.async_set("test.entity", 12)

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    assert len(service_calls) == 2

    hass.states.async_set("test.entity", 9)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[0].data["id"] == 0
async def test_if_fires_on_entity_change_uuid(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test for firing on entity change."""
    context = Context()

    entry = entity_registry.async_get_or_create(
        "test", "hue", "1234", suggested_object_id="beer"
    )

    assert entry.entity_id == "test.beer"

    hass.states.async_set("test.beer", "hello")
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {"platform": "state", "entity_id": entry.id},
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": (
                            "{{ trigger.platform }}"
                            " - {{ trigger.entity_id }}"
                            " - {{ trigger.from_state.state }}"
                            " - {{ trigger.to_state.state }}"
                            " - {{ trigger.for }}"
                            " - {{ trigger.id }}"
                        )
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set("test.beer", "world", context=context)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].context.parent_id == context.id
    assert (
        service_calls[0].data["some"] == "state - test.beer - hello - world - None - 0"
    )

    await hass.services.async_call(
        automation.DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_MATCH_ALL},
        blocking=True,
    )
    assert len(service_calls) == 2
    hass.states.async_set("test.beer", "planet")
    await hass.async_block_till_done()
    assert len(service_calls) == 2
async def test_if_fires_on_entity_creation_and_removal(
    hass: HomeAssistant, service_calls: list[ServiceCall]
) -> None:
    """Test for firing on entity creation and removal, with to/from constraints."""
    # set automations for multiple combinations to/from
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {"platform": "state", "entity_id": "test.entity_0"},
                    "action": {"service": "test.automation"},
                },
                {
                    "trigger": {
                        "platform": "state",
                        "from": "hello",
                        "entity_id": "test.entity_1",
                    },
                    "action": {"service": "test.automation"},
                },
                {
                    "trigger": {
                        "platform": "state",
                        "to": "world",
                        "entity_id": "test.entity_2",
                    },
                    "action": {"service": "test.automation"},
                },
            ],
        },
    )
    await hass.async_block_till_done()

    # use contexts to identify trigger entities
    context_0 = Context()
    context_1 = Context()
    context_2 = Context()

    # automation with match_all triggers on creation
    hass.states.async_set("test.entity_0", "any", context=context_0)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].context.parent_id == context_0.id

    # create entities, trigger on test.entity_2 ('to' matches, no 'from')
    hass.states.async_set("test.entity_1", "hello", context=context_1)
    hass.states.async_set("test.entity_2", "world", context=context_2)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].context.parent_id == context_2.id

    # removal of both, trigger on test.entity_1 ('from' matches, no 'to')
    assert hass.states.async_remove("test.entity_1", context=context_1)
    assert hass.states.async_remove("test.entity_2", context=context_2)
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].context.parent_id == context_1.id

    # automation with match_all triggers on removal
    assert hass.states.async_remove("test.entity_0", context=context_0)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert service_calls[3].context.parent_id == context_0.id
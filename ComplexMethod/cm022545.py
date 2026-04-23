async def test_if_fires_on_entities_change_overlap_for_template(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    service_calls: list[ServiceCall],
    above: int | str,
    below: int | str,
) -> None:
    """Test for firing on entities change with overlap and for template."""
    hass.states.async_set("test.entity_1", 0)
    hass.states.async_set("test.entity_2", 0)
    await hass.async_block_till_done()

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "trigger": {
                    "platform": "numeric_state",
                    "entity_id": ["test.entity_1", "test.entity_2"],
                    "above": above,
                    "below": below,
                    "for": '{{ 5 if trigger.entity_id == "test.entity_1" else 10 }}',
                },
                "action": {
                    "service": "test.automation",
                    "data_template": {
                        "some": "{{ trigger.entity_id }} - {{ trigger.for }}"
                    },
                },
            }
        },
    )
    await hass.async_block_till_done()

    hass.states.async_set("test.entity_1", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 15)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=1))
    async_fire_time_changed(hass)
    hass.states.async_set("test.entity_2", 9)
    await hass.async_block_till_done()
    assert len(service_calls) == 0
    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "test.entity_1 - 0:00:05"

    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "test.entity_2 - 0:00:10"
async def test_light_color_different_than_custom(
    hass: HomeAssistant,
    client: MagicMock,
    config_entry: MockConfigEntry,
    integration_setup: Callable[[MagicMock], Awaitable[bool]],
    entity_id: str,
    events: dict[EventKey, Any],
    appliance: HomeAppliance,
) -> None:
    """Test that light color attributes are not set if color is different than custom."""
    assert await integration_setup(client)
    assert config_entry.state is ConfigEntryState.LOADED
    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_RGB_COLOR: (255, 255, 0),
            ATTR_ENTITY_ID: entity_id,
        },
    )
    await hass.async_block_till_done()
    entity_state = hass.states.get(entity_id)
    assert entity_state is not None
    assert entity_state.state == STATE_ON
    assert entity_state.attributes[ATTR_RGB_COLOR] is not None
    assert entity_state.attributes[ATTR_HS_COLOR] is not None

    await client.add_events(
        [
            EventMessage(
                appliance.ha_id,
                EventType.NOTIFY,
                ArrayOfEvents(
                    [
                        Event(
                            key=event_key,
                            raw_key=event_key.value,
                            timestamp=0,
                            level="",
                            handling="",
                            value=value,
                        )
                        for event_key, value in events.items()
                    ]
                ),
            )
        ]
    )
    await hass.async_block_till_done()

    entity_state = hass.states.get(entity_id)
    assert entity_state is not None
    assert entity_state.state == STATE_ON
    assert entity_state.attributes[ATTR_RGB_COLOR] is None
    assert entity_state.attributes[ATTR_HS_COLOR] is None
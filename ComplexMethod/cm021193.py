async def test_if_fires_on_turn_on_request(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test for turn_on triggers firing."""
    await setup_lgnetcast(hass)

    device = device_registry.async_get_device(identifiers={(DOMAIN, UNIQUE_ID)})
    assert device is not None

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device.id,
                        "type": "lg_netcast.turn_on",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": "{{ trigger.device_id }}",
                            "id": "{{ trigger.id }}",
                        },
                    },
                },
                {
                    "trigger": {
                        "platform": "lg_netcast.turn_on",
                        "entity_id": ENTITY_ID,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "some": ENTITY_ID,
                            "id": "{{ trigger.id }}",
                        },
                    },
                },
            ],
        },
    )

    await hass.services.async_call(
        "media_player",
        "turn_on",
        {"entity_id": ENTITY_ID},
        blocking=True,
    )

    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[1].data["some"] == device.id
    assert service_calls[1].data["id"] == 0
    assert service_calls[2].data["some"] == ENTITY_ID
    assert service_calls[2].data["id"] == 0
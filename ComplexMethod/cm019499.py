async def test_if_fires_on_state_change(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    service_calls: list[ServiceCall],
) -> None:
    """Test triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_OFF)

    data_template = (
        "{label} - {{{{ trigger.platform}}}} - "
        "{{{{ trigger.entity_id}}}} - {{{{ trigger.from_state.state}}}} - "
        "{{{{ trigger.to_state.state}}}} - {{{{ trigger.for }}}}"
    )
    trigger_types = {
        "buffering",
        "changed_states",
        "idle",
        "paused",
        "playing",
        "turned_off",
        "turned_on",
    }

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "entity_id": entry.id,
                        "type": trigger,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": data_template.format(label=trigger)},
                    },
                }
                for trigger in trigger_types
            ]
        },
    )

    # Fake that the entity is turning on.
    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert {service_calls[0].data["some"], service_calls[1].data["some"]} == {
        "turned_on - device - media_player.test_5678 - off - on - None",
        "changed_states - device - media_player.test_5678 - off - on - None",
    }

    # Fake that the entity is turning off.
    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    assert len(service_calls) == 4
    assert {service_calls[2].data["some"], service_calls[3].data["some"]} == {
        "turned_off - device - media_player.test_5678 - on - off - None",
        "changed_states - device - media_player.test_5678 - on - off - None",
    }

    # Fake that the entity becomes idle.
    hass.states.async_set(entry.entity_id, STATE_IDLE)
    await hass.async_block_till_done()
    assert len(service_calls) == 6
    assert {service_calls[4].data["some"], service_calls[5].data["some"]} == {
        "idle - device - media_player.test_5678 - off - idle - None",
        "changed_states - device - media_player.test_5678 - off - idle - None",
    }

    # Fake that the entity starts playing.
    hass.states.async_set(entry.entity_id, STATE_PLAYING)
    await hass.async_block_till_done()
    assert len(service_calls) == 8
    assert {service_calls[6].data["some"], service_calls[7].data["some"]} == {
        "playing - device - media_player.test_5678 - idle - playing - None",
        "changed_states - device - media_player.test_5678 - idle - playing - None",
    }

    # Fake that the entity is paused.
    hass.states.async_set(entry.entity_id, STATE_PAUSED)
    await hass.async_block_till_done()
    assert len(service_calls) == 10
    assert {service_calls[8].data["some"], service_calls[9].data["some"]} == {
        "paused - device - media_player.test_5678 - playing - paused - None",
        "changed_states - device - media_player.test_5678 - playing - paused - None",
    }

    # Fake that the entity is buffering.
    hass.states.async_set(entry.entity_id, STATE_BUFFERING)
    await hass.async_block_till_done()
    assert len(service_calls) == 12
    assert {service_calls[10].data["some"], service_calls[11].data["some"]} == {
        "buffering - device - media_player.test_5678 - paused - buffering - None",
        "changed_states - device - media_player.test_5678 - paused - buffering - None",
    }
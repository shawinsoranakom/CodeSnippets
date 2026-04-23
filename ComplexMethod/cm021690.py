async def test_player_config_expose_to_ha_toggle(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    music_assistant_client: MagicMock,
) -> None:
    """Test player exposure toggle via config update."""
    await setup_integration_from_fixtures(hass, music_assistant_client)
    await hass.async_block_till_done()
    config_entry = hass.config_entries.async_entries(DOMAIN)[0]

    # Initial state: player should be exposed (from fixture)
    entity_id = "media_player.test_player_1"
    player_id = "00:00:00:00:00:01"
    assert hass.states.get(entity_id)
    assert entity_registry.async_get(entity_id)
    device_entry = device_registry.async_get_device({(DOMAIN, player_id)})
    assert device_entry
    assert player_id in config_entry.runtime_data.discovered_players

    # Simulate player config update: expose_to_ha = False
    # Trigger the subscription callback
    event_data = {
        "player_id": player_id,
        "provider": "test",
        "values": {
            ATTR_CONF_EXPOSE_PLAYER_TO_HA: {
                "key": ATTR_CONF_EXPOSE_PLAYER_TO_HA,
                "type": "boolean",
                "value": False,
                "label": ATTR_CONF_EXPOSE_PLAYER_TO_HA,
                "default_value": True,
            }
        },
    }
    await trigger_subscription_callback(
        hass,
        music_assistant_client,
        EventType.PLAYER_CONFIG_UPDATED,
        player_id,
        event_data,
    )

    # Verify player was removed from HA
    assert player_id not in config_entry.runtime_data.discovered_players
    assert not hass.states.get(entity_id)
    assert not entity_registry.async_get(entity_id)
    device_entry = device_registry.async_get_device({(DOMAIN, player_id)})
    assert not device_entry

    # Now test re-adding the player: expose_to_ha = True
    await trigger_subscription_callback(
        hass,
        music_assistant_client,
        EventType.PLAYER_CONFIG_UPDATED,
        player_id,
        {
            "player_id": player_id,
            "provider": "test",
            "values": {
                ATTR_CONF_EXPOSE_PLAYER_TO_HA: {
                    "key": ATTR_CONF_EXPOSE_PLAYER_TO_HA,
                    "type": "boolean",
                    "value": True,
                    "label": ATTR_CONF_EXPOSE_PLAYER_TO_HA,
                    "default_value": True,
                }
            },
        },
    )

    # Verify player was re-added to HA
    assert player_id in config_entry.runtime_data.discovered_players
    assert hass.states.get(entity_id)
    assert entity_registry.async_get(entity_id)
    device_entry = device_registry.async_get_device({(DOMAIN, player_id)})
    assert device_entry
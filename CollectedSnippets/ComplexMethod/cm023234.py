async def test_zwave_js_trigger_config_entry_unloaded(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    client,
    lock_schlage_be469,
    integration,
) -> None:
    """Test zwave_js triggers bypass dynamic validation when needed."""
    device = device_registry.async_get_device(
        identifiers={get_device_id(client.driver, lock_schlage_be469)}
    )
    assert device

    # Test bypass check is False
    assert not async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.value_updated",
            "options": {
                "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                "command_class": CommandClass.DOOR_LOCK.value,
                "property": "latchStatus",
            },
        },
    )

    await hass.config_entries.async_unload(integration.entry_id)

    # Test full validation for both events
    assert await TRIGGERS["value_updated"].async_validate_complete_config(
        hass,
        {
            "platform": f"{DOMAIN}.value_updated",
            "options": {
                "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                "command_class": CommandClass.DOOR_LOCK.value,
                "property": "latchStatus",
            },
        },
    )

    assert await TRIGGERS["event"].async_validate_complete_config(
        hass,
        {
            "platform": f"{DOMAIN}.event",
            "options": {
                "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                "event_source": "node",
                "event": "interview stage completed",
            },
        },
    )

    # Test bypass check
    assert async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.value_updated",
            "options": {
                "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                "command_class": CommandClass.DOOR_LOCK.value,
                "property": "latchStatus",
            },
        },
    )

    assert async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.value_updated",
            "options": {
                "device_id": device.id,
                "command_class": CommandClass.DOOR_LOCK.value,
                "property": "latchStatus",
                "from": "ajar",
            },
        },
    )

    assert async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.event",
            "options": {
                "entity_id": SCHLAGE_BE469_LOCK_ENTITY,
                "event_source": "node",
                "event": "interview stage completed",
            },
        },
    )

    assert async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.event",
            "options": {
                "device_id": device.id,
                "event_source": "node",
                "event": "interview stage completed",
                "event_data": {"stageName": "ProtocolInfo"},
            },
        },
    )

    assert async_bypass_dynamic_config_validation(
        hass,
        {
            "platform": f"{DOMAIN}.event",
            "options": {
                "config_entry_id": integration.entry_id,
                "event_source": "controller",
                "event": "nvm convert progress",
            },
        },
    )
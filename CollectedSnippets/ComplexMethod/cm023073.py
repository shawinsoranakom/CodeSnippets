async def test_get_action_capabilities_legacy(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test we get the expected capabilities from a select action."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_option",
        "entity_id": entry.entity_id,
        "option": "option1",
    }

    # Test when entity doesn't exists
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities
    assert "extra_fields" in capabilities
    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "option",
            "required": True,
            "type": "select",
            "options": [],
        },
    ]

    # Mock an entity
    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )

    # Test if we get the right capabilities now
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities
    assert "extra_fields" in capabilities
    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "option",
            "required": True,
            "type": "select",
            "options": [("option1", "option1"), ("option2", "option2")],
        },
    ]

    # Test next/previous actions
    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_next",
        "entity_id": entry.entity_id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities
    assert "extra_fields" in capabilities
    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "cycle",
            "optional": True,
            "required": False,
            "type": "boolean",
            "default": True,
        },
    ]

    config["type"] = "select_previous"
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities
    assert "extra_fields" in capabilities
    assert voluptuous_serialize.convert(
        capabilities["extra_fields"], custom_serializer=cv.custom_serializer
    ) == [
        {
            "name": "cycle",
            "optional": True,
            "required": False,
            "type": "boolean",
            "default": True,
        },
    ]

    # Test action types without extra fields
    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_first",
        "entity_id": entry.entity_id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities == {}

    config["type"] = "select_last"
    capabilities = await async_get_action_capabilities(hass, config)
    assert capabilities == {}
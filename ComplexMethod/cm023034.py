async def test_fuzzy_matching(
    hass: HomeAssistant,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
    fuzzy_matching: bool,
    sentence: str,
    intent_type: str,
    slots: dict[str, Any],
) -> None:
    """Test fuzzy vs. non-fuzzy matching on some English sentences."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "conversation", {})
    assert await async_setup_component(hass, "intent", {})
    await light_intent.async_setup_intents(hass)

    agent = async_get_agent(hass)
    agent.fuzzy_matching = fuzzy_matching

    area_office = area_registry.async_get_or_create("office_id")
    area_office = area_registry.async_update(area_office.id, name="office")

    entry = MockConfigEntry()
    entry.add_to_hass(hass)
    office_satellite = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections=set(),
        identifiers={("demo", "id-1234")},
    )
    device_registry.async_update_device(office_satellite.id, area_id=area_office.id)

    office_light = entity_registry.async_get_or_create(
        "light", "demo", "1234", original_name="office light"
    )
    office_light = entity_registry.async_update_entity(
        office_light.entity_id, area_id=area_office.id
    )
    hass.states.async_set(
        office_light.entity_id,
        "on",
        attributes={
            ATTR_FRIENDLY_NAME: "office light",
            ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS, ColorMode.RGB],
        },
    )
    _on_calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    result = await conversation.async_converse(
        hass,
        sentence,
        None,
        Context(),
        language="en",
        device_id=office_satellite.id,
    )
    response = result.response

    if not fuzzy_matching:
        # Should not match
        assert response.response_type == intent.IntentResponseType.ERROR
        return

    assert response.response_type in (
        intent.IntentResponseType.ACTION_DONE,
        intent.IntentResponseType.QUERY_ANSWER,
    )
    assert response.intent is not None
    assert response.intent.intent_type == intent_type

    # Verify slot texts match
    actual_slots = {
        slot_name: slot_value["text"]
        for slot_name, slot_value in response.intent.slots.items()
        if slot_name != "preferred_area_id"  # context area
    }
    assert actual_slots == slots
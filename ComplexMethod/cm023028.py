async def test_turn_on_area(
    hass: HomeAssistant,
    init_components,
    area_registry: ar.AreaRegistry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test turning on an area."""
    entry = MockConfigEntry(domain="test")
    entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    kitchen_area = area_registry.async_create("kitchen")
    device_registry.async_update_device(device.id, area_id=kitchen_area.id)

    entity_registry.async_get_or_create(
        "light", "demo", "1234", suggested_object_id="stove"
    )
    entity_registry.async_update_entity(
        "light.stove",
        aliases=[er.COMPUTED_NAME, "my stove light"],
        area_id=kitchen_area.id,
    )
    hass.states.async_set("light.stove", "off")

    calls = async_mock_service(hass, LIGHT_DOMAIN, "turn_on")

    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the kitchen"},
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    call = calls[0]
    assert call.domain == LIGHT_DOMAIN
    assert call.service == "turn_on"
    assert call.data == {"entity_id": ["light.stove"]}

    basement_area = area_registry.async_create("basement")
    device_registry.async_update_device(device.id, area_id=basement_area.id)
    entity_registry.async_update_entity("light.stove", area_id=basement_area.id)
    calls.clear()

    # Test that the area is updated
    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the kitchen"},
    )
    await hass.async_block_till_done()

    assert len(calls) == 0

    # Test the new area works
    await hass.services.async_call(
        "conversation",
        "process",
        {conversation.ATTR_TEXT: "turn on lights in the basement"},
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    call = calls[0]
    assert call.domain == LIGHT_DOMAIN
    assert call.service == "turn_on"
    assert call.data == {"entity_id": ["light.stove"]}
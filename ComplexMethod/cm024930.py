async def test_extract_from_service_label_id(hass: HomeAssistant) -> None:
    """Test the extraction using label ID as reference."""
    entities = [
        MockEntity(name="with_my_label", entity_id="light.with_my_label"),
        MockEntity(name="no_labels", entity_id="light.no_labels"),
        MockEntity(
            name="with_labels_from_device", entity_id="light.with_labels_from_device"
        ),
    ]

    call = ServiceCall(hass, "light", "turn_on", {"label_id": "label_area"})
    extracted = await service.async_extract_entities(hass, entities, call)
    assert len(extracted) == 1
    assert extracted[0].entity_id == "light.with_labels_from_device"

    call = ServiceCall(hass, "light", "turn_on", {"label_id": "my-label"})
    extracted = await service.async_extract_entities(hass, entities, call)
    assert len(extracted) == 1
    assert extracted[0].entity_id == "light.with_my_label"

    call = ServiceCall(hass, "light", "turn_on", {"label_id": ["my-label", "label1"]})
    extracted = await service.async_extract_entities(hass, entities, call)
    assert len(extracted) == 2
    assert sorted(ent.entity_id for ent in extracted) == [
        "light.with_labels_from_device",
        "light.with_my_label",
    ]

    call = ServiceCall(
        hass,
        "light",
        "turn_on",
        {"label_id": ["my-label", "label1"], "device_id": "device-no-labels"},
    )
    extracted = await service.async_extract_entities(hass, entities, call)
    assert len(extracted) == 3
    assert sorted(ent.entity_id for ent in extracted) == [
        "light.no_labels",
        "light.with_labels_from_device",
        "light.with_my_label",
    ]
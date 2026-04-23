def test_entity_registry_items() -> None:
    """Test the EntityRegistryItems container."""
    entities = er.EntityRegistryItems()
    assert entities.get_entity_id(("a", "b", "c")) is None
    assert entities.get_entry("abc") is None

    entry1 = RegistryEntryWithDefaults(
        entity_id="test.entity1", unique_id="1234", platform="hue"
    )
    entry2 = RegistryEntryWithDefaults(
        entity_id="test.entity2", unique_id="2345", platform="hue"
    )
    entities["test.entity1"] = entry1
    entities["test.entity2"] = entry2

    assert entities["test.entity1"] is entry1
    assert entities["test.entity2"] is entry2

    assert entities.get_entity_id(("test", "hue", "1234")) is entry1.entity_id
    assert entities.get_entry(entry1.id) is entry1
    assert entities.get_entity_id(("test", "hue", "2345")) is entry2.entity_id
    assert entities.get_entry(entry2.id) is entry2

    entities.pop("test.entity1")
    del entities["test.entity2"]

    assert entities.get_entity_id(("test", "hue", "1234")) is None
    assert entities.get_entry(entry1.id) is None
    assert entities.get_entity_id(("test", "hue", "2345")) is None
    assert entities.get_entry(entry2.id) is None
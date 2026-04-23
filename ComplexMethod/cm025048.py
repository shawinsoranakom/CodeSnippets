def test_registry_items(
    registry_items: NormalizedNameBaseRegistryItems[NormalizedNameBaseRegistryEntry],
) -> None:
    """Test registry items."""
    entry = NormalizedNameBaseRegistryEntry(name="Hello World")
    registry_items["key"] = entry
    assert registry_items["key"] == entry
    assert list(registry_items.values()) == [entry]
    assert registry_items.get_by_name("Hello World") == entry

    # test update entry
    entry2 = NormalizedNameBaseRegistryEntry(name="Hello World 2")
    registry_items["key"] = entry2
    assert registry_items["key"] == entry2
    assert list(registry_items.values()) == [entry2]
    assert registry_items.get_by_name("Hello World 2") == entry2

    # test delete entry
    del registry_items["key"]
    assert "key" not in registry_items
    assert not registry_items.values()
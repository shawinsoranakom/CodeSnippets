async def test_cached_entity_properties(
    hass: HomeAssistant, property: str, default_value: Any, values: Any
) -> None:
    """Test entity properties are cached."""
    ent1 = entity.Entity()
    ent2 = entity.Entity()
    assert getattr(ent1, property) == default_value
    assert type(getattr(ent1, property)) is type(default_value)
    assert getattr(ent2, property) == default_value
    assert type(getattr(ent2, property)) is type(default_value)

    # Test set
    setattr(ent1, f"_attr_{property}", values[0])
    assert getattr(ent1, property) == values[0]
    assert type(getattr(ent1, property)) is type(values[0])
    assert getattr(ent2, property) == default_value
    assert type(getattr(ent2, property)) is type(default_value)

    # Test update
    setattr(ent1, f"_attr_{property}", values[1])
    assert getattr(ent1, property) == values[1]
    assert type(getattr(ent1, property)) is type(values[1])
    assert getattr(ent2, property) == default_value
    assert type(getattr(ent2, property)) is type(default_value)

    # Test delete
    delattr(ent1, f"_attr_{property}")
    assert getattr(ent1, property) == default_value
    assert type(getattr(ent1, property)) is type(default_value)
    assert getattr(ent2, property) == default_value
    assert type(getattr(ent2, property)) is type(default_value)
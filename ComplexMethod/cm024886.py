async def test_cached_entity_property_delete_attr(hass: HomeAssistant) -> None:
    """Test deleting an _attr corresponding to a cached property."""
    property_name = "has_entity_name"

    ent = entity.Entity()
    assert not hasattr(ent, f"_attr_{property_name}")
    with pytest.raises(AttributeError):
        delattr(ent, f"_attr_{property_name}")
    assert getattr(ent, property_name) is False

    with pytest.raises(AttributeError):
        delattr(ent, f"_attr_{property_name}")
    assert not hasattr(ent, f"_attr_{property_name}")
    assert getattr(ent, property_name) is False

    setattr(ent, f"_attr_{property_name}", True)
    assert getattr(ent, property_name) is True

    delattr(ent, f"_attr_{property_name}")
    assert not hasattr(ent, f"_attr_{property_name}")
    assert getattr(ent, property_name) is False
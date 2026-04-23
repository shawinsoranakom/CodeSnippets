async def test_async_get_areas_by_alias_collisions(
    area_registry: ar.AreaRegistry,
) -> None:
    """Make sure we can get the areas by alias when the aliases have collisions."""
    area = area_registry.async_create("Mock1")
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == []

    # Add an alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1"})
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == [updated_area]

    # Add a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1", "alias  1"})
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == [updated_area]

    # Add a colliding alias
    updated_area = area_registry.async_update(
        area.id, aliases={"alias1", "alias 1", "alias  1"}
    )
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == [updated_area]

    # Remove a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1", "alias  1"})
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == [updated_area]

    # Remove a colliding alias
    updated_area = area_registry.async_update(area.id, aliases={"alias1"})
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == [updated_area]

    # Remove all aliases
    updated_area = area_registry.async_update(area.id, aliases={})
    assert area_registry.async_get_areas_by_alias("A l i a s 1") == []
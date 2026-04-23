async def test_async_get_floors_by_alias_collisions(
    floor_registry: fr.FloorRegistry,
) -> None:
    """Make sure we can get the floors by alias when the aliases have collisions."""
    floor = floor_registry.async_create("First floor")
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == []

    # Add an alias
    updated_floor = floor_registry.async_update(floor.floor_id, aliases={"alias1"})
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == [updated_floor]

    # Add a colliding alias
    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias  1"}
    )
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == [updated_floor]

    # Add a colliding alias
    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias 1", "alias  1"}
    )
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == [updated_floor]

    # Remove a colliding alias
    updated_floor = floor_registry.async_update(
        floor.floor_id, aliases={"alias1", "alias  1"}
    )
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == [updated_floor]

    # Remove a colliding alias
    updated_floor = floor_registry.async_update(floor.floor_id, aliases={"alias1"})
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == [updated_floor]

    # Remove all aliases
    updated_floor = floor_registry.async_update(floor.floor_id, aliases={})
    assert floor_registry.async_get_floors_by_alias("A l i a s 1") == []
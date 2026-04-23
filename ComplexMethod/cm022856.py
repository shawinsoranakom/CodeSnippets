async def test_storage_resources_create_preserves_existing(
    hass: HomeAssistant,
    hass_storage: dict[str, Any],
) -> None:
    """Test async_create_item lazy-loads before writing.

    Custom integrations may call async_create_item() during startup before the
    frontend triggers a resource listing. Without a lazy-load guard, the
    collection is empty and async_create_item() overwrites all existing
    resources on disk.
    """
    resource_config = [{**item, "id": uuid.uuid4().hex} for item in RESOURCE_EXAMPLES]
    hass_storage[resources.RESOURCE_STORAGE_KEY] = {
        "key": resources.RESOURCE_STORAGE_KEY,
        "version": 1,
        "data": {"items": resource_config},
    }
    assert await async_setup_component(hass, "lovelace", {})

    resource_collection = hass.data[LOVELACE_DATA].resources

    # Directly call async_create_item before any websocket listing
    await resource_collection.async_create_item(
        {"res_type": "module", "url": "/local/new.js"}
    )

    # Existing resources must still be present
    items = resource_collection.async_items()
    assert len(items) == len(resource_config) + 1
    urls = [item["url"] for item in items]
    for original in resource_config:
        assert original["url"] in urls
    assert "/local/new.js" in urls
async def test_browse_media_camera(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    ufp: MockUFPFixture,
    doorbell: Camera,
    camera: Camera,
) -> None:
    """Test browsing camera selector level media."""

    ufp.api.get_bootstrap = AsyncMock(return_value=ufp.api.bootstrap)
    await init_entry(hass, ufp, [doorbell, camera])

    ufp.api.bootstrap.auth_user.all_permissions = [
        Permission.unifi_dict_to_dict(
            {"rawPermission": "camera:create,read,write,delete,deletemedia:*"}
        ),
        Permission.unifi_dict_to_dict(
            {"rawPermission": f"camera:readmedia:{doorbell.id}"}
        ),
    ]

    entity_registry.async_update_entity(
        "camera.test_camera_high_resolution_channel",
        disabled_by=er.RegistryEntryDisabler("user"),
    )
    await hass.async_block_till_done()

    source = await async_get_media_source(hass)
    media_item = MediaSourceItem(hass, DOMAIN, "test_id:browse", None)

    browse = await source.async_browse_media(media_item)

    assert browse.title == "UnifiProtect"
    assert browse.identifier == "test_id:browse"
    assert len(browse.children) == 2
    assert browse.children[0].title == "All Cameras"
    assert browse.children[0].identifier == "test_id:browse:all"
    assert browse.children[1].title == doorbell.name
    assert browse.children[1].identifier == f"test_id:browse:{doorbell.id}"
    assert browse.children[1].thumbnail is None
async def test_supported_device(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry, setup_platform
) -> None:
    """Test a media source with a supported camera."""
    await setup_platform()

    assert len(hass.states.async_all()) == 1
    camera = hass.states.get("camera.front")
    assert camera is not None

    device = device_registry.async_get_device(identifiers={(DOMAIN, DEVICE_ID)})
    assert device
    assert device.name == DEVICE_NAME

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}")
    assert browse.domain == DOMAIN
    assert browse.title == "Nest"
    assert browse.identifier == ""
    assert browse.can_expand
    assert len(browse.children) == 1
    assert browse.children[0].domain == DOMAIN
    assert browse.children[0].identifier == device.id
    assert browse.children[0].title == "Front: Recent Events"

    browse = await async_browse_media(hass, f"{URI_SCHEME}{DOMAIN}/{device.id}")
    assert browse.domain == DOMAIN
    assert browse.identifier == device.id
    assert browse.title == "Front: Recent Events"
    assert len(browse.children) == 0
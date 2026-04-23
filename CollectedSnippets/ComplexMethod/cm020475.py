async def test_automatic_module_device_addition_and_removal(
    hass: HomeAssistant,
    mock_camera_config_entry: MockConfigEntry,
    mock_connect: AsyncMock,
    mock_discovery: AsyncMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    freezer: FrozenDateTimeFactory,
    platform: str,
    modules: list[str],
    features: list[str],
    translated_name: str | None,
    child_device_type: DeviceType,
) -> None:
    """Test for automatic device with modules addition and removal."""

    children = {
        f"child{index}": _mocked_device(
            alias=f"child {index}",
            modules=modules,
            features=features,
            device_type=child_device_type,
            device_id=f"child{index}",
        )
        for index in range(1, 5)
    }

    mock_device = _mocked_device(
        alias="hub",
        children=[children["child1"], children["child2"]],
        features=["ssid"],
        device_type=DeviceType.Hub,
        device_id="hub_parent",
        ip_address=IP_ADDRESS3,
        mac=MAC_ADDRESS3,
    )
    # Set the parent property for the dynamic children as mock_device only sets
    # it on initialization
    for child in children.values():
        child.parent = mock_device

    with override_side_effect(mock_connect["connect"], lambda *_, **__: mock_device):
        mock_camera_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_camera_config_entry.entry_id)
        await hass.async_block_till_done()

    for child_id in (1, 2):
        sub_id = f"_{translated_name}" if translated_name else ""
        entity_id = f"{platform}.child_{child_id}{sub_id}"
        state = hass.states.get(entity_id)
        assert state
        assert entity_registry.async_get(entity_id)

    parent_device = device_registry.async_get_device(
        identifiers={(DOMAIN, "hub_parent")}
    )
    assert parent_device

    for device_id in ("child1", "child2"):
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        assert device_entry
        assert device_entry.via_device_id == parent_device.id

    # Remove one of the devices
    mock_device.children = [children["child1"]]
    freezer.tick(5)
    async_fire_time_changed(hass)

    sub_id = f"_{translated_name}" if translated_name else ""
    entity_id = f"{platform}.child_2{sub_id}"
    state = hass.states.get(entity_id)
    assert state is None
    assert entity_registry.async_get(entity_id) is None

    assert device_registry.async_get_device(identifiers={(DOMAIN, "child2")}) is None

    # Re-dd the previously removed child device
    mock_device.children = [
        children["child1"],
        children["child2"],
    ]
    freezer.tick(5)
    async_fire_time_changed(hass)

    for child_id in (1, 2):
        sub_id = f"_{translated_name}" if translated_name else ""
        entity_id = f"{platform}.child_{child_id}{sub_id}"
        state = hass.states.get(entity_id)
        assert state
        assert entity_registry.async_get(entity_id)

    for device_id in ("child1", "child2"):
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        assert device_entry
        assert device_entry.via_device_id == parent_device.id

    # Add child devices
    mock_device.children = [children["child1"], children["child3"], children["child4"]]
    freezer.tick(5)
    async_fire_time_changed(hass)

    for child_id in (1, 3, 4):
        sub_id = f"_{translated_name}" if translated_name else ""
        entity_id = f"{platform}.child_{child_id}{sub_id}"
        state = hass.states.get(entity_id)
        assert state
        assert entity_registry.async_get(entity_id)

    for device_id in ("child1", "child3", "child4"):
        assert device_registry.async_get_device(identifiers={(DOMAIN, device_id)})

    # Add the previously removed child device
    mock_device.children = [
        children["child1"],
        children["child2"],
        children["child3"],
        children["child4"],
    ]
    freezer.tick(5)
    async_fire_time_changed(hass)

    for child_id in (1, 2, 3, 4):
        sub_id = f"_{translated_name}" if translated_name else ""
        entity_id = f"{platform}.child_{child_id}{sub_id}"
        state = hass.states.get(entity_id)
        assert state
        assert entity_registry.async_get(entity_id)

    for device_id in ("child1", "child2", "child3", "child4"):
        device_entry = device_registry.async_get_device(
            identifiers={(DOMAIN, device_id)}
        )
        assert device_entry
        assert device_entry.via_device_id == parent_device.id
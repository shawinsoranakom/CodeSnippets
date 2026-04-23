async def test_loading_saving_data(
    hass: HomeAssistant, device_registry: dr.DeviceRegistry
) -> None:
    """Test that we load/save data correctly."""
    config_entry_1 = MockConfigEntry()
    config_entry_1.add_to_hass(hass)
    config_entry_2 = MockConfigEntry()
    config_entry_2.add_to_hass(hass)
    config_entry_3 = MockConfigEntry()
    config_entry_3.add_to_hass(hass)
    config_entry_4 = MockConfigEntry()
    config_entry_4.add_to_hass(hass)
    config_entry_5 = MockConfigEntry()
    config_entry_5.add_to_hass(hass)

    orig_via = device_registry.async_get_or_create(
        config_entry_id=config_entry_1.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        identifiers={("hue", "0123")},
        manufacturer="manufacturer",
        model="via",
        name="Original Name",
        sw_version="Orig SW 1",
        entry_type=None,
    )

    orig_light = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections=set(),
        identifiers={("hue", "456")},
        manufacturer="manufacturer",
        model="light",
        via_device=("hue", "0123"),
        disabled_by=dr.DeviceEntryDisabler.USER,
    )

    orig_light2 = device_registry.async_get_or_create(
        config_entry_id=config_entry_2.entry_id,
        connections=set(),
        identifiers={("hue", "789")},
        manufacturer="manufacturer",
        model="light",
        via_device=("hue", "0123"),
    )

    device_registry.async_remove_device(orig_light2.id)

    orig_light3 = device_registry.async_get_or_create(
        config_entry_id=config_entry_3.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "34:56:AB:CD:EF:12")},
        identifiers={("hue", "abc")},
        manufacturer="manufacturer",
        model="light",
    )

    device_registry.async_get_or_create(
        config_entry_id=config_entry_4.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "34:56:AB:CD:EF:12")},
        identifiers={("abc", "123")},
        manufacturer="manufacturer",
        model="light",
    )

    device_registry.async_remove_device(orig_light3.id)

    orig_light4 = device_registry.async_get_or_create(
        config_entry_id=config_entry_3.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "34:56:AB:CD:EF:12")},
        identifiers={("hue", "abc")},
        manufacturer="manufacturer",
        model="light",
        entry_type=dr.DeviceEntryType.SERVICE,
    )

    assert orig_light4.id == orig_light3.id

    orig_kitchen_light = device_registry.async_get_or_create(
        config_entry_id=config_entry_5.entry_id,
        connections=set(),
        identifiers={("hue", "999")},
        manufacturer="manufacturer",
        model="light",
        via_device=("hue", "0123"),
        disabled_by=dr.DeviceEntryDisabler.USER,
        suggested_area="Kitchen",
    )

    assert len(device_registry.devices) == 4
    assert len(device_registry.deleted_devices) == 1

    orig_via = device_registry.async_update_device(
        orig_via.id,
        area_id="mock-area-id",
        name_by_user="mock-name-by-user",
        labels={"mock-label1", "mock-label2"},
    )

    # Now load written data in new registry
    registry2 = dr.DeviceRegistry(hass)
    await flush_store(device_registry._store)
    registry2.async_setup()
    await registry2.async_load()

    # Ensure same order
    assert list(device_registry.devices) == list(registry2.devices)
    assert list(device_registry.deleted_devices) == list(registry2.deleted_devices)

    new_via = registry2.async_get_device(identifiers={("hue", "0123")})
    new_light = registry2.async_get_device(identifiers={("hue", "456")})
    new_light4 = registry2.async_get_device(identifiers={("hue", "abc")})

    assert orig_via == new_via
    assert orig_light == new_light
    assert orig_light4 == new_light4

    # Ensure enums converted
    for old, new in (
        (orig_via, new_via),
        (orig_light, new_light),
        (orig_light4, new_light4),
    ):
        assert old.disabled_by is new.disabled_by
        assert old.entry_type is new.entry_type

    # Ensure a save/load cycle does not keep suggested area
    new_kitchen_light = registry2.async_get_device(identifiers={("hue", "999")})
    assert orig_kitchen_light.area_id == "kitchen"

    orig_kitchen_light_without_suggested_area = device_registry.async_update_device(
        orig_kitchen_light.id, suggested_area=None
    )
    assert orig_kitchen_light_without_suggested_area.area_id == "kitchen"
    assert orig_kitchen_light_without_suggested_area == new_kitchen_light
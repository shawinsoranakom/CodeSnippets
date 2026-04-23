async def test_iid_generation_and_restore_v2(
    hass: HomeAssistant, iid_storage, hass_storage: dict[str, Any]
) -> None:
    """Test generating iids and restoring them from storage."""
    entry = MockConfigEntry(domain=DOMAIN)

    iid_storage = AccessoryIIDStorage(hass, entry.entry_id)
    await iid_storage.async_initialize()
    not_accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "000000AA-0000-1000-8000-0026BB765291", None, None, None
    )
    assert not_accessory_info_service_iid == 2
    assert iid_storage.allocated_iids == {"1": [1, 2]}
    not_accessory_info_service_iid_2 = iid_storage.get_or_allocate_iid(
        1, "000000BB-0000-1000-8000-0026BB765291", None, None, None
    )
    assert not_accessory_info_service_iid_2 == 3
    assert iid_storage.allocated_iids == {"1": [1, 2, 3]}
    not_accessory_info_service_iid_2 = iid_storage.get_or_allocate_iid(
        1, "000000BB-0000-1000-8000-0026BB765291", None, None, None
    )
    assert not_accessory_info_service_iid_2 == 3
    assert iid_storage.allocated_iids == {"1": [1, 2, 3]}
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    assert accessory_info_service_iid == 1
    assert iid_storage.allocated_iids == {"1": [1, 2, 3]}
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        1, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    assert accessory_info_service_iid == 1
    assert iid_storage.allocated_iids == {"1": [1, 2, 3]}
    accessory_info_service_iid = iid_storage.get_or_allocate_iid(
        2, "0000003E-0000-1000-8000-0026BB765291", None, None, None
    )
    assert accessory_info_service_iid == 1
    assert iid_storage.allocated_iids == {"1": [1, 2, 3], "2": [1]}
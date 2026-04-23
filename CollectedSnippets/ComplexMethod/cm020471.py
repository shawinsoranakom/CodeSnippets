async def test_unlink_devices(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    caplog: pytest.LogCaptureFixture,
    device_id,
    id_count,
    domains,
    expected_message,
) -> None:
    """Test for unlinking child device ids."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={**CREATE_ENTRY_DATA_LEGACY},
        entry_id="123456",
        unique_id="any",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)

    # Generate list of test identifiers
    test_identifiers = [
        (domain, f"{device_id}{'' if i == 0 else f'_000{i}'}")
        for i in range(id_count)
        for domain in domains
    ]
    update_msg_fragment = "identifiers for device dummy (hs300):"
    update_msg = f"{expected_message} {update_msg_fragment}" if expected_message else ""

    # Expected identifiers should include all other domains or all the newer non-mac device ids
    # or just the parent mac device id
    expected_identifiers = [
        (domain, device_id)
        for domain, device_id in test_identifiers
        if domain != DOMAIN
        or device_id.startswith(DEVICE_ID)
        or device_id == DEVICE_ID_MAC
    ]

    device_registry.async_get_or_create(
        config_entry_id="123456",
        connections={
            (dr.CONNECTION_NETWORK_MAC, MAC_ADDRESS),
        },
        identifiers=set(test_identifiers),
        model="hs300",
        name="dummy",
    )
    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    assert device_entries[0].connections == {
        (dr.CONNECTION_NETWORK_MAC, MAC_ADDRESS),
    }
    assert device_entries[0].identifiers == set(test_identifiers)

    with (
        patch("homeassistant.components.tplink.CONF_CONFIG_ENTRY_MINOR_VERSION", 3),
        _patch_discovery(),
        _patch_single_discovery(),
        _patch_connect(),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    device_entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)

    assert device_entries[0].connections == {(dr.CONNECTION_NETWORK_MAC, MAC_ADDRESS)}

    assert device_entries[0].identifiers == set(expected_identifiers)
    assert entry.version == 1
    assert entry.minor_version == 3

    assert update_msg in caplog.text
    assert "Migration to version 1.3 complete" in caplog.text
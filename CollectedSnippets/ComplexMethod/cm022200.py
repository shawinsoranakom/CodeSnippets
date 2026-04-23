async def disconnected_source_mock(
    hass: HomeAssistant,
    upnp_factory_mock: Mock,
    config_entry_mock: MockConfigEntry,
    ssdp_scanner_mock: Mock,
    dms_device_mock: Mock,
) -> AsyncIterable[None]:
    """Fixture to set up a mock DmsDeviceSource in a disconnected state."""
    # Cause the connection attempt to fail
    upnp_factory_mock.async_create_device.side_effect = UpnpConnectionError

    config_entry_mock.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry_mock.entry_id)
    await hass.async_block_till_done()

    # Check the DmsDeviceSource has registered all needed listeners
    assert len(config_entry_mock.update_listeners) == 0
    assert ssdp_scanner_mock.async_register_callback.await_count == 2
    assert ssdp_scanner_mock.async_register_callback.return_value.call_count == 0

    # Make async_browse_metadata work for assert_source_available when this
    # source is connected
    didl_item = didl_lite.Item(
        id=DUMMY_OBJECT_ID,
        restricted=False,
        title="Object",
        res=[didl_lite.Resource(uri="foo/bar", protocol_info="http-get:*:audio/mpeg:")],
    )
    dms_device_mock.async_browse_metadata.return_value = didl_item

    # Run the test
    yield

    # Unload config entry to clean up
    assert await hass.config_entries.async_remove(config_entry_mock.entry_id) == {
        "require_restart": False
    }

    # Check device source has cleaned up its resources
    assert not config_entry_mock.update_listeners
    assert (
        ssdp_scanner_mock.async_register_callback.await_count
        == ssdp_scanner_mock.async_register_callback.return_value.call_count
    )
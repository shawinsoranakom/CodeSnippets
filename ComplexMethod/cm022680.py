async def test_homekit_start(
    hass: HomeAssistant,
    hk_driver,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test HomeKit start method."""
    entry = await async_init_integration(hass)

    homekit = _mock_homekit(hass, entry, HOMEKIT_MODE_BRIDGE)

    homekit.bridge = Mock()
    homekit.bridge.accessories = []
    homekit.driver = hk_driver
    acc = Accessory(hk_driver, "any")
    homekit.driver.accessory = acc

    connection = (dr.CONNECTION_NETWORK_MAC, "AA:BB:CC:DD:EE:FF")
    bridge_with_wrong_mac = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={connection},
        manufacturer="Any",
        name="Any",
        model="Home Assistant HomeKit Bridge",
    )

    hass.states.async_set("light.demo", "on")
    hass.states.async_set("light.demo2", "on")
    state = hass.states.async_all()[0]

    with (
        patch(f"{PATH_HOMEKIT}.HomeKit.add_bridge_accessory") as mock_add_acc,
        patch(f"{PATH_HOMEKIT}.async_show_setup_message") as mock_setup_msg,
        patch("pyhap.accessory_driver.AccessoryDriver.async_start") as hk_driver_start,
    ):
        await homekit.async_start()

    await hass.async_block_till_done()
    mock_add_acc.assert_any_call(state)
    mock_setup_msg.assert_called_with(
        hass, entry.entry_id, "Mock Title (Home Assistant Bridge)", ANY, ANY
    )
    assert hk_driver_start.called
    assert homekit.status == STATUS_RUNNING

    # Test start() if already started
    hk_driver_start.reset_mock()
    await homekit.async_start()
    await hass.async_block_till_done()
    assert not hk_driver_start.called

    assert device_registry.async_get(bridge_with_wrong_mac.id) is None

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.entry_id, BRIDGE_SERIAL_NUMBER)}
    )
    assert device
    formatted_mac = dr.format_mac(homekit.driver.state.mac)
    assert (dr.CONNECTION_NETWORK_MAC, formatted_mac) in device.connections

    # Start again to make sure the registry entry is kept
    homekit.status = STATUS_READY
    with (
        patch(f"{PATH_HOMEKIT}.HomeKit.add_bridge_accessory") as mock_add_acc,
        patch(f"{PATH_HOMEKIT}.async_show_setup_message") as mock_setup_msg,
        patch("pyhap.accessory_driver.AccessoryDriver.async_start") as hk_driver_start,
        patch("pyhap.accessory_driver.AccessoryDriver.load") as load_mock,
        patch("pyhap.accessory_driver.AccessoryDriver.persist") as persist_mock,
        patch(f"{PATH_HOMEKIT}.os.path.exists", return_value=True),
    ):
        await homekit.async_stop()
        await homekit.async_start()

    assert load_mock.called
    assert not persist_mock.called
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, entry.entry_id, BRIDGE_SERIAL_NUMBER)}
    )
    assert device
    formatted_mac = dr.format_mac(homekit.driver.state.mac)
    assert (dr.CONNECTION_NETWORK_MAC, formatted_mac) in device.connections
    assert device.model == "HomeBridge"

    assert len(device_registry.devices) == 1
    assert homekit.driver.state.config_version == 1
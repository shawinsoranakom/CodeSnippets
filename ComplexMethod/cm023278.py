async def test_reconfigure_migrate_with_addon(
    hass: HomeAssistant,
    client: MagicMock,
    device_registry: dr.DeviceRegistry,
    multisensor_6: Node,
    integration: MockConfigEntry,
    restart_addon: AsyncMock,
    addon_options: dict[str, Any],
    set_addon_options: AsyncMock,
    get_server_version: AsyncMock,
    form_data: dict[str, Any],
    new_addon_options: dict,
    restore_server_version_side_effect: Exception | None,
    final_unique_id: str,
    keep_old_devices: bool,
    device_entry_count: int,
) -> None:
    """Test migration flow with add-on."""
    version_info = get_server_version.return_value
    entry = integration
    assert client.connect.call_count == 1
    assert client.driver.controller.home_id == 3245146787
    assert entry.unique_id == "3245146787"
    hass.config_entries.async_update_entry(
        entry,
        data={
            "url": "ws://localhost:3000",
            "use_addon": True,
            "usb_path": "/dev/ttyUSB0",
        },
    )
    addon_options["device"] = "/dev/ttyUSB0"

    controller_node = client.driver.controller.own_node
    controller_device_id = (
        f"{client.driver.controller.home_id}-{controller_node.node_id}"
    )
    controller_device_id_ext = (
        f"{controller_device_id}-{controller_node.manufacturer_id}:"
        f"{controller_node.product_type}:{controller_node.product_id}"
    )

    assert len(device_registry.devices) == 2
    # Verify there's a device entry for the controller.
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, controller_device_id)}
    )
    assert device
    assert device == device_registry.async_get_device(
        identifiers={(DOMAIN, controller_device_id_ext)}
    )
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW090"
    assert device.name == "Z‐Stick Gen5 USB Controller"
    # Verify there's a device entry for the multisensor.
    sensor_device_id = f"{client.driver.controller.home_id}-{multisensor_6.node_id}"
    device = device_registry.async_get_device(identifiers={(DOMAIN, sensor_device_id)})
    assert device
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW100"
    assert device.name == "Multisensor 6"
    # Customize the sensor device name.
    device_registry.async_update_device(
        device.id, name_by_user="Custom Sensor Device Name"
    )

    async def mock_backup_nvm_raw():
        await asyncio.sleep(0)
        client.driver.controller.emit(
            "nvm backup progress", {"bytesRead": 100, "total": 200}
        )
        return b"test_nvm_data"

    client.driver.controller.async_backup_nvm_raw = AsyncMock(
        side_effect=mock_backup_nvm_raw
    )

    async def mock_restore_nvm(data: bytes, options: dict[str, bool] | None = None):
        client.driver.controller.emit(
            "nvm convert progress",
            {"event": "nvm convert progress", "bytesRead": 100, "total": 200},
        )
        await asyncio.sleep(0)
        client.driver.controller.emit(
            "nvm restore progress",
            {"event": "nvm restore progress", "bytesWritten": 100, "total": 200},
        )
        client.driver.controller.data["homeId"] = 3245146787
        client.driver.emit(
            "driver ready", {"event": "driver ready", "source": "driver"}
        )

    client.driver.controller.async_restore_nvm = AsyncMock(side_effect=mock_restore_nvm)

    events = async_capture_events(
        hass, data_entry_flow.EVENT_DATA_ENTRY_FLOW_PROGRESS_UPDATE
    )

    result = await entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_migrate"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "backup_nvm"

    with patch("pathlib.Path.write_bytes") as mock_file:
        await hass.async_block_till_done()
        assert client.driver.controller.async_backup_nvm_raw.call_count == 1
        assert mock_file.call_count == 1
        assert len(events) == 1
        assert events[0].data["progress"] == 0.5
        events.clear()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "instruct_unplug"
    assert entry.state is config_entries.ConfigEntryState.NOT_LOADED

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "choose_serial_port"

    version_info.home_id = 5678

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], form_data
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"
    assert set_addon_options.call_args == call(
        "core_zwave_js", AddonsOptions(config=new_addon_options)
    )

    # Simulate the new connected controller hardware labels.
    # This will cause a new device entry to be created
    # when the config entry is loaded before restoring NVM.
    controller_node = client.driver.controller.own_node
    controller_node.data["manufacturerId"] = 999
    controller_node.data["productId"] = 999
    controller_node.device_config.data["description"] = "New Device Name"
    controller_node.device_config.data["label"] = "New Device Model"
    controller_node.device_config.data["manufacturer"] = "New Device Manufacturer"
    client.driver.controller.data["homeId"] = 5678

    await hass.async_block_till_done()

    assert restart_addon.call_args == call("core_zwave_js")

    # Ensure add-on running would migrate the old settings back into the config entry
    with patch("homeassistant.components.zwave_js.async_ensure_addon_running"):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        assert entry.unique_id == "5678"
        get_server_version.side_effect = restore_server_version_side_effect
        version_info.home_id = 3245146787

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "restore_nvm"
        assert client.connect.call_count == 2

        await hass.async_block_till_done()
    assert client.connect.call_count == 4
    assert entry.state is config_entries.ConfigEntryState.LOADED
    assert client.driver.controller.async_restore_nvm.call_count == 1
    assert len(events) == 2
    assert events[0].data["progress"] == 0.25
    assert events[1].data["progress"] == 0.75

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "migration_successful"
    assert entry.data["url"] == "ws://host1:3001"
    assert entry.data[CONF_USB_PATH] == new_addon_options.get(CONF_ADDON_DEVICE)
    assert entry.data[CONF_SOCKET_PATH] == new_addon_options.get(CONF_ADDON_SOCKET)
    assert entry.data["use_addon"] is True
    assert ("keep_old_devices" in entry.data) is keep_old_devices
    assert entry.unique_id == final_unique_id

    assert len(device_registry.devices) == device_entry_count
    controller_device_id_ext = (
        f"{controller_device_id}-{controller_node.manufacturer_id}:"
        f"{controller_node.product_type}:{controller_node.product_id}"
    )
    device = device_registry.async_get_device(
        identifiers={(DOMAIN, controller_device_id_ext)}
    )
    assert device
    assert device.manufacturer == "New Device Manufacturer"
    assert device.model == "New Device Model"
    assert device.name == "New Device Name"
    device = device_registry.async_get_device(identifiers={(DOMAIN, sensor_device_id)})
    assert device
    assert device.manufacturer == "AEON Labs"
    assert device.model == "ZW100"
    assert device.name == "Multisensor 6"
    assert device.name_by_user == "Custom Sensor Device Name"
    assert client.driver.controller.home_id == 3245146787
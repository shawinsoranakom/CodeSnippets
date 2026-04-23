async def test_find_flows_by_init_data_type(manager: MockFlowManager) -> None:
    """Test we can find flows by init data type."""

    @dataclasses.dataclass
    class BluetoothDiscoveryData:
        """Bluetooth Discovery data."""

        address: str

    @dataclasses.dataclass
    class WiFiDiscoveryData:
        """WiFi Discovery data."""

        address: str

    @manager.mock_reg_handler("test")
    class TestFlow(data_entry_flow.FlowHandler):
        VERSION = 1

        async def async_step_first(self, user_input=None):
            if user_input is not None:
                return await self.async_step_second()
            return self.async_show_form(step_id="first", data_schema=vol.Schema([str]))

        async def async_step_second(self, user_input=None):
            if user_input is not None:
                return self.async_create_entry(
                    title="Test Entry",
                    data={"init": self.init_data, "user": user_input},
                )
            return self.async_show_form(step_id="second", data_schema=vol.Schema([str]))

    bluetooth_data = BluetoothDiscoveryData("aa:bb:cc:dd:ee:ff")
    wifi_data = WiFiDiscoveryData("host")

    bluetooth_form = await manager.async_init(
        "test", context={"init_step": "first"}, data=bluetooth_data
    )
    await manager.async_init("test", context={"init_step": "first"}, data=wifi_data)

    assert (
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData, lambda data: True
            )
        )
    ) == 1
    assert (
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData,
                lambda data: bool(data.address == "aa:bb:cc:dd:ee:ff"),
            )
        )
    ) == 1
    assert (
        len(
            manager.async_progress_by_init_data_type(
                BluetoothDiscoveryData, lambda data: bool(data.address == "not it")
            )
        )
    ) == 0

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    assert len(wifi_flows) == 1

    bluetooth_result = await manager.async_configure(
        bluetooth_form["flow_id"], ["SECOND-DATA"]
    )
    assert bluetooth_result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert len(manager.async_progress()) == 1
    assert len(manager.mock_created_entries) == 1
    result = manager.mock_created_entries[0]
    assert result["handler"] == "test"
    assert result["data"] == {"init": bluetooth_data, "user": ["SECOND-DATA"]}

    bluetooth_flows = manager.async_progress_by_init_data_type(
        BluetoothDiscoveryData, lambda data: True
    )
    assert len(bluetooth_flows) == 0

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    assert len(wifi_flows) == 1

    manager.async_abort(wifi_flows[0]["flow_id"])

    wifi_flows = manager.async_progress_by_init_data_type(
        WiFiDiscoveryData, lambda data: True
    )
    assert len(wifi_flows) == 0
    assert len(manager.async_progress()) == 0
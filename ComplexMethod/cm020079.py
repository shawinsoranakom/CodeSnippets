async def test_if_fires_on_telegram(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    device_registry: dr.DeviceRegistry,
    knx: KNXTestKit,
) -> None:
    """Test telegram device triggers firing."""
    await knx.setup_integration()
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, f"_{knx.mock_config_entry.entry_id}_interface")}
    )

    # "id" field added to action to test if `trigger_data` passed correctly in `async_attach_trigger`
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                # "catch_all" trigger
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "type": "telegram",
                        "group_value_write": True,
                        "group_value_response": True,
                        "group_value_read": True,
                        "incoming": True,
                        "outgoing": True,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "catch_all": ("telegram - {{ trigger.destination }}"),
                            "id": (" {{ trigger.id }}"),
                        },
                    },
                },
                # "specific" trigger
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "id": "test-id",
                        "type": "telegram",
                        "destination": [
                            "1/2/3",
                            "1/516",  # "1/516" -> "1/2/4" in 2level format
                        ],
                        "group_value_write": True,
                        "group_value_response": False,
                        "group_value_read": False,
                        "incoming": True,
                        "outgoing": False,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "specific": ("telegram - {{ trigger.destination }}"),
                            "id": (" {{ trigger.id }}"),
                        },
                    },
                },
            ]
        },
    )

    # "specific" shall ignore destination address
    await knx.receive_write("0/0/1", (0x03, 0x2F))
    assert len(service_calls) == 1
    test_call = service_calls.pop()
    assert test_call.data["catch_all"] == "telegram - 0/0/1"
    assert test_call.data["id"] == 0

    await knx.receive_write("1/2/4", (0x03, 0x2F))
    assert len(service_calls) == 2
    test_call = service_calls.pop()
    assert test_call.data["specific"] == "telegram - 1/2/4"
    assert test_call.data["id"] == "test-id"
    test_call = service_calls.pop()
    assert test_call.data["catch_all"] == "telegram - 1/2/4"
    assert test_call.data["id"] == 0

    # "specific" shall ignore GroupValueRead
    await knx.receive_read("1/2/4")
    assert len(service_calls) == 1
    test_call = service_calls.pop()
    assert test_call.data["catch_all"] == "telegram - 1/2/4"
    assert test_call.data["id"] == 0
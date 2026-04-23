async def test_telegram_trigger(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    knx: KNXTestKit,
) -> None:
    """Test telegram triggers firing."""
    await knx.setup_integration()

    # "id" field added to action to test if `trigger_data` passed correctly in `async_attach_trigger`
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                # "catch_all" trigger
                {
                    "trigger": {
                        "platform": "knx.telegram",
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
                        "platform": "knx.telegram",
                        "id": "test-id",
                        "destination": ["1/2/3", 2564],  # 2564 -> "1/2/4" in raw format
                        "group_value_write": True,
                        "group_value_response": False,
                        "group_value_read": False,
                        "incoming": True,
                        "outgoing": True,
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
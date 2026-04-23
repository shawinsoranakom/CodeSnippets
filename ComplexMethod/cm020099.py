async def test_telegram_trigger_dpt_option(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    knx: KNXTestKit,
    payload: tuple[int, ...],
    type_option: dict[str, bool],
    expected_value: int | None,
    expected_unit: str | None,
) -> None:
    """Test telegram trigger type option."""
    await knx.setup_integration()
    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                # "catch_all" trigger
                {
                    "trigger": {
                        "platform": "knx.telegram",
                        **type_option,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "catch_all": ("telegram - {{ trigger.destination }}"),
                            "trigger": (" {{ trigger }}"),
                        },
                    },
                },
            ]
        },
    )
    await knx.receive_write("0/0/1", payload)

    assert len(service_calls) == 1
    test_call = service_calls.pop()
    assert test_call.data["catch_all"] == "telegram - 0/0/1"
    assert test_call.data["trigger"]["value"] == expected_value
    assert test_call.data["trigger"]["unit"] == expected_unit

    await knx.receive_read("0/0/1")

    assert len(service_calls) == 1
    test_call = service_calls.pop()
    assert test_call.data["catch_all"] == "telegram - 0/0/1"
    assert test_call.data["trigger"]["value"] is None
    assert test_call.data["trigger"]["unit"] is None
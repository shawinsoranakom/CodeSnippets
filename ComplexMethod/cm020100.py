async def test_telegram_trigger_options(
    hass: HomeAssistant,
    service_calls: list[ServiceCall],
    knx: KNXTestKit,
    group_value_options: dict[str, bool],
    direction_options: dict[str, bool],
) -> None:
    """Test telegram trigger options."""
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
                        **group_value_options,
                        **direction_options,
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {
                            "catch_all": ("telegram - {{ trigger.destination }}"),
                        },
                    },
                },
            ]
        },
    )
    await knx.receive_write("0/0/1", 1)
    if group_value_options.get("group_value_write", True) and direction_options.get(
        "incoming", True
    ):
        assert len(service_calls) == 1
        assert service_calls.pop().data["catch_all"] == "telegram - 0/0/1"
    else:
        assert len(service_calls) == 0

    await knx.receive_response("0/0/1", 1)
    if group_value_options["group_value_response"] and direction_options.get(
        "incoming", True
    ):
        assert len(service_calls) == 1
        assert service_calls.pop().data["catch_all"] == "telegram - 0/0/1"
    else:
        assert len(service_calls) == 0

    await knx.receive_read("0/0/1")
    if group_value_options["group_value_read"] and direction_options.get(
        "incoming", True
    ):
        assert len(service_calls) == 1
        assert service_calls.pop().data["catch_all"] == "telegram - 0/0/1"
    else:
        assert len(service_calls) == 0

    await hass.services.async_call(
        "knx",
        "send",
        {"address": "0/0/1", "payload": True},
        blocking=True,
    )
    assert len(service_calls) == 1

    await knx.assert_write("0/0/1", True)
    if (
        group_value_options.get("group_value_write", True)
        and direction_options["outgoing"]
    ):
        assert len(service_calls) == 2
        assert service_calls.pop().data["catch_all"] == "telegram - 0/0/1"
    else:
        assert len(service_calls) == 1
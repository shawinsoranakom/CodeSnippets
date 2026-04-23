async def test_switch_device(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, qs_devices
) -> None:
    """Test a switch device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {"switches": ["@a00001"]}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_start()
    await hass.async_block_till_done()

    # verify initial state is off per the 'val' in qs_devices
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "off"

    # ask hass to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=100", json={"data": "OK"})
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await asyncio.sleep(0.01)
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=100"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    # verify state is on
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "on"

    # ask hass to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00001=0", json={"data": "OK"})
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": "switch.switch_1"}, blocking=True
    )
    await hass.async_block_till_done()
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00001=0"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    # verify state is off
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "off"

    # check if setting the value in the network show in hass
    qs_devices[0]["val"] = "ON"
    listen_mock.queue_response(json=EMPTY_PACKET)
    await hass.async_block_till_done()
    state_obj = hass.states.get("switch.switch_1")
    assert state_obj.state == "on"

    listen_mock.stop()
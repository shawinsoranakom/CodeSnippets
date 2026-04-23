async def test_light_device(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, qs_devices
) -> None:
    """Test a light device."""

    async def get_devices_json(method, url, data):
        return AiohttpClientMockResponse(method=method, url=url, json=qs_devices)

    config = {"qwikswitch": {}}
    aioclient_mock.get("http://127.0.0.1:2020/&device", side_effect=get_devices_json)
    listen_mock = MockLongPollSideEffect()
    aioclient_mock.get("http://127.0.0.1:2020/&listen", side_effect=listen_mock)
    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_start()
    await hass.async_block_till_done()

    # verify initial state is on per the 'val' in qs_devices
    state_obj = hass.states.get("light.dim_3")
    assert state_obj.state == "on"
    assert state_obj.attributes["brightness"] == 255

    # ask hass to turn off and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=0", json={"data": "OK"})
    await hass.services.async_call(
        "light", "turn_off", {"entity_id": "light.dim_3"}, blocking=True
    )
    await asyncio.sleep(0.01)
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00003=0"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    state_obj = hass.states.get("light.dim_3")
    assert state_obj.state == "off"

    # change brightness in network and check that hass updates
    qs_devices[2]["val"] = "280c55"  # half dimmed
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    assert state_obj.state == "on"
    assert 16 < state_obj.attributes["brightness"] < 240

    # turn off in the network and see that it is off in hass as well
    qs_devices[2]["val"] = "280c78"  # off
    listen_mock.queue_response(json=EMPTY_PACKET)
    await asyncio.sleep(0.01)
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    assert state_obj.state == "off"

    # ask hass to turn on and verify command is sent to device
    aioclient_mock.mock_calls.clear()
    aioclient_mock.get("http://127.0.0.1:2020/@a00003=100", json={"data": "OK"})
    await hass.services.async_call(
        "light", "turn_on", {"entity_id": "light.dim_3"}, blocking=True
    )
    await hass.async_block_till_done()
    assert (
        "GET",
        URL("http://127.0.0.1:2020/@a00003=100"),
        None,
        None,
    ) in aioclient_mock.mock_calls
    await hass.async_block_till_done()
    state_obj = hass.states.get("light.dim_3")
    assert state_obj.state == "on"

    listen_mock.stop()
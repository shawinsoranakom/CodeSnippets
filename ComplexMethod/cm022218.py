async def test_emoncms_send_data(
    hass: HomeAssistant,
    emoncms_client: AsyncMock,
    caplog: pytest.LogCaptureFixture,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test sending data to Emoncms with and without success."""

    config = {
        "emoncms_history": {
            "api_key": "dummy",
            "url": "http://fake-url",
            "inputnode": 42,
            "whitelist": ["sensor.temp"],
        }
    }

    assert await async_setup_component(hass, "emoncms_history", config)
    await hass.async_block_till_done()

    for state in None, "", STATE_UNAVAILABLE, STATE_UNKNOWN:
        hass.states.async_set("sensor.temp", state, {"unit_of_measurement": "°C"})
        await hass.async_block_till_done()

        freezer.tick(timedelta(seconds=60))
        await hass.async_block_till_done()

        assert emoncms_client.async_input_post.call_args is None

    hass.states.async_set("sensor.temp", "not_a_number", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    emoncms_client.async_input_post.assert_not_called()

    hass.states.async_set("sensor.temp", "23.4", {"unit_of_measurement": "°C"})
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    emoncms_client.async_input_post.assert_called_once()
    assert emoncms_client.async_input_post.return_value == '{"success": true}'

    _, kwargs = emoncms_client.async_input_post.call_args
    assert kwargs["data"] == {"sensor.temp": 23.4}
    assert kwargs["node"] == "42"

    emoncms_client.async_input_post.side_effect = aiohttp.ClientError(
        "Connection refused"
    )
    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    assert any(
        "Network error when sending data to Emoncms" in message
        for message in caplog.text.splitlines()
    )

    emoncms_client.async_input_post.side_effect = ValueError("Invalid value format")

    await hass.async_block_till_done()

    freezer.tick(timedelta(seconds=60))
    await hass.async_block_till_done()

    assert any(
        "Value error when preparing data for Emoncms" in message
        for message in caplog.text.splitlines()
    )
async def test_on_connect(hass: HomeAssistant) -> None:
    """Test cloud on connect triggers."""
    cl = hass.data[DATA_CLOUD]

    assert len(cl.iot._on_connect) == 3

    assert len(hass.states.async_entity_ids("binary_sensor")) == 0

    cloud_states = []

    def handle_state(cloud_state):
        nonlocal cloud_states
        cloud_states.append(cloud_state)

    async_listen_connection_change(hass, handle_state)

    assert "async_setup" in str(cl.iot._on_connect[-1])
    await cl.iot._on_connect[-1]()
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("binary_sensor")) == 0

    # The on_start callback discovers the binary sensor platform
    assert "async_setup" in str(cl._on_start[-1])
    await cl._on_start[-1]()
    await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids("binary_sensor")) == 1

    with patch("homeassistant.helpers.discovery.async_load_platform") as mock_load:
        await cl._on_start[-1]()
        await hass.async_block_till_done()

    assert len(mock_load.mock_calls) == 0

    assert len(cloud_states) == 1
    assert cloud_states[-1] == CloudConnectionState.CLOUD_CONNECTED

    await cl.iot._on_connect[-1]()
    await hass.async_block_till_done()
    assert len(cloud_states) == 2
    assert cloud_states[-1] == CloudConnectionState.CLOUD_CONNECTED

    assert len(cl.iot._on_disconnect) == 2
    assert "async_setup" in str(cl.iot._on_disconnect[-1])
    await cl.iot._on_disconnect[-1]()
    await hass.async_block_till_done()

    assert len(cloud_states) == 3
    assert cloud_states[-1] == CloudConnectionState.CLOUD_DISCONNECTED

    await cl.iot._on_disconnect[-1]()
    await hass.async_block_till_done()
    assert len(cloud_states) == 4
    assert cloud_states[-1] == CloudConnectionState.CLOUD_DISCONNECTED
async def test_update_supervisor_progress(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    supervisor_info: AsyncMock,
) -> None:
    """Test progress reporting for a Supervisor update that was not initiated via the entity.

    Covers CLI-triggered and Supervisor self-update flows: the entity must
    show download progress from job events and stay in the installing state
    across the Supervisor restart until the coordinator observes the new
    installed version.
    """
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        assert await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    message_id = 0
    job_uuid = uuid4().hex
    entity_id = "update.home_assistant_supervisor_update"

    def make_job_message(progress: float, done: bool | None) -> dict[str, Any]:
        nonlocal message_id
        message_id += 1
        return {
            "id": message_id,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "uuid": job_uuid,
                    "created": "2025-09-29T00:00:00.000000+00:00",
                    "name": "supervisor_update",
                    "reference": None,
                    "progress": progress,
                    "done": done,
                    "stage": None,
                    "extra": {"total": 1234567890} if progress > 0 else None,
                    "errors": [],
                },
            },
        }

    await client.send_json(make_job_message(progress=0, done=None))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes.get("in_progress") is False
    assert hass.states.get(entity_id).attributes.get("update_percentage") is None

    await client.send_json(make_job_message(progress=5, done=False))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes.get("in_progress") is True
    assert hass.states.get(entity_id).attributes.get("update_percentage") == 5

    await client.send_json(make_job_message(progress=50, done=False))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes.get("update_percentage") == 50

    # Job done: download finished, Supervisor is about to restart. The entity
    # must stay in the installing state until the new version is observed.
    await client.send_json(make_job_message(progress=100, done=True))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes.get("in_progress") is True
    assert hass.states.get(entity_id).attributes.get("update_percentage") is None

    # New Supervisor comes up and fires STARTUP_COMPLETE.
    supervisor_info.return_value = replace(
        supervisor_info.return_value,
        version="1.0.1dev222",
        update_available=False,
    )
    await client.send_json(
        {
            "id": message_id + 1,
            "type": "supervisor/event",
            "data": {
                "event": "supervisor_update",
                "update_key": "supervisor",
                "data": {"startup": "complete"},
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]

    async_fire_time_changed(
        hass, dt_util.utcnow() + timedelta(seconds=REQUEST_REFRESH_DELAY + 1)
    )
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).attributes.get("in_progress") is False
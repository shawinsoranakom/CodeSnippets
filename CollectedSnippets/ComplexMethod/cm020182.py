async def test_update_core_progress(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test progress reporting for core update."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        assert result
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)
    message_id = 0
    job_uuid = uuid4().hex

    def make_job_message(
        progress: float, done: bool | None, errors: list[dict[str, str]] | None = None
    ):
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
                    "name": "home_assistant_core_update",
                    "reference": None,
                    "progress": progress,
                    "done": done,
                    "stage": None,
                    "extra": {"total": 1234567890} if progress > 0 else None,
                    "errors": errors or [],
                },
            },
        }

    await client.send_json(make_job_message(progress=0, done=None))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
        is False
    )
    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
        is None
    )

    await client.send_json(make_job_message(progress=5, done=False))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
        is True
    )
    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
        == 5
    )

    await client.send_json(make_job_message(progress=50, done=False))
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
        is True
    )
    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
        == 50
    )

    # During a successful update Home Assistant is stopped before the update job
    # reaches the end. An error ends it early so we use that for test
    await client.send_json(
        make_job_message(
            progress=70,
            done=True,
            errors=[
                {"type": "HomeAssistantUpdateError", "message": "bad", "stage": None}
            ],
        )
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "in_progress"
        )
        is False
    )
    assert (
        hass.states.get("update.home_assistant_core_update").attributes.get(
            "update_percentage"
        )
        is None
    )
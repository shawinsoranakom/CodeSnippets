async def test_job_manager_ws_updates(
    hass: HomeAssistant, jobs_info: AsyncMock, hass_ws_client: WebSocketGenerator
) -> None:
    """Test job updates sync from Supervisor WS messages."""
    result = await async_setup_component(hass, "hassio", {})
    assert result
    jobs_info.assert_called_once()

    jobs_info.reset_mock()
    client = await hass_ws_client(hass)
    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    assert not data_coordinator.jobs.current_jobs

    # Make an example listener
    job_data: Job | None = None

    @callback
    def mock_subcription_callback(job: Job) -> None:
        nonlocal job_data
        job_data = job

    subscription = JobSubscription(
        mock_subcription_callback, name="test_job", reference="test"
    )
    unsubscribe = data_coordinator.jobs.subscribe(subscription)

    # Send start of job update
    await client.send_json(
        {
            "id": 1,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": (uuid := uuid4().hex),
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": (created := datetime.now().isoformat()),
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    assert job_data.progress == 0
    assert job_data.done is False
    # One job in the cache
    assert len(data_coordinator.jobs.current_jobs) == 1

    # Example progress update
    await client.send_json(
        {
            "id": 2,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": uuid,
                    "progress": 50,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    assert job_data.progress == 50
    assert job_data.done is False
    # Same job, same number of jobs in cache
    assert len(data_coordinator.jobs.current_jobs) == 1

    # Unrelated job update - name change, subscriber should not receive
    await client.send_json(
        {
            "id": 3,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "bad_job",
                    "reference": "test",
                    "uuid": uuid4().hex,
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    # New job, cache increases
    assert len(data_coordinator.jobs.current_jobs) == 2

    # Unrelated job update - reference change, subscriber should not receive
    await client.send_json(
        {
            "id": 4,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "bad",
                    "uuid": uuid4().hex,
                    "progress": 0,
                    "stage": None,
                    "done": False,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    # New job, cache increases
    assert len(data_coordinator.jobs.current_jobs) == 3

    # Unsubscribe mock listener, should not receive final update
    unsubscribe()
    await client.send_json(
        {
            "id": 5,
            "type": "supervisor/event",
            "data": {
                "event": "job",
                "data": {
                    "name": "test_job",
                    "reference": "test",
                    "uuid": uuid,
                    "progress": 100,
                    "stage": None,
                    "done": True,
                    "errors": [],
                    "created": created,
                    "extra": None,
                },
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    assert job_data.progress == 50
    assert job_data.done is False
    # Job ended, cache decreases
    assert len(data_coordinator.jobs.current_jobs) == 2

    # REST API should not be used during this sequence
    jobs_info.assert_not_called()
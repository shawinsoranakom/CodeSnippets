async def test_job_manager_reload_on_supervisor_restart(
    hass: HomeAssistant, jobs_info: AsyncMock, hass_ws_client: WebSocketGenerator
) -> None:
    """Test job manager reloads cache on supervisor restart."""
    jobs_info.return_value = JobsInfo(
        ignore_conditions=[],
        jobs=[
            Job(
                name="test_job",
                reference="test",
                uuid=uuid4(),
                progress=0,
                stage=None,
                done=False,
                errors=[],
                created=datetime.now(),
                extra=None,
                child_jobs=[],
            )
        ],
    )

    result = await async_setup_component(hass, "hassio", {})
    assert result
    jobs_info.assert_called_once()

    data_coordinator: HassioMainDataUpdateCoordinator = hass.data[MAIN_COORDINATOR]
    assert len(data_coordinator.jobs.current_jobs) == 1
    assert data_coordinator.jobs.current_jobs[0].name == "test_job"

    jobs_info.reset_mock()
    jobs_info.return_value = JobsInfo(ignore_conditions=[], jobs=[])
    client = await hass_ws_client(hass)

    # Make an example listener
    job_data: Job | None = None

    @callback
    def mock_subcription_callback(job: Job) -> None:
        nonlocal job_data
        job_data = job

    subscription = JobSubscription(mock_subcription_callback, name="test_job")
    data_coordinator.jobs.subscribe(subscription)

    # Send supervisor restart signal
    await client.send_json(
        {
            "id": 1,
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
    await hass.async_block_till_done()

    # Listener should be told job is done and cache cleared out
    jobs_info.assert_called_once()
    assert job_data.name == "test_job"
    assert job_data.reference == "test"
    assert job_data.done is True
    assert not data_coordinator.jobs.current_jobs
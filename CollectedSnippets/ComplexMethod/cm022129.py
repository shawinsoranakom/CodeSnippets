async def test_logbook_many_entities_multiple_calls(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the logbook view with a many entities called multiple times."""
    await async_setup_component(hass, "logbook", {})
    await async_setup_component(hass, "automation", {})

    await async_recorder_block_till_done(hass)
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    for automation_id in range(5):
        hass.bus.async_fire(
            EVENT_AUTOMATION_TRIGGERED,
            {
                ATTR_NAME: f"Mock automation {automation_id}",
                ATTR_ENTITY_ID: f"automation.mock_{automation_id}_automation",
            },
        )
    await async_wait_recording_done(hass)
    client = await hass_client()

    # Today time 00:00:00
    start = dt_util.utcnow().date()
    start_date = datetime(start.year, start.month, start.day, tzinfo=dt_util.UTC)
    end_time = start + timedelta(hours=24)

    for automation_id in range(5):
        # Test today entries with filter by end_time
        response = await client.get(
            f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_{automation_id}_automation"
        )
        assert response.status == HTTPStatus.OK
        json_dict = await response.json()

        assert len(json_dict) == 1
        assert (
            json_dict[0]["entity_id"] == f"automation.mock_{automation_id}_automation"
        )

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_0_automation,automation.mock_1_automation,automation.mock_2_automation"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert len(json_dict) == 3
    assert json_dict[0]["entity_id"] == "automation.mock_0_automation"
    assert json_dict[1]["entity_id"] == "automation.mock_1_automation"
    assert json_dict[2]["entity_id"] == "automation.mock_2_automation"

    response = await client.get(
        f"/api/logbook/{start_date.isoformat()}?end_time={end_time}&entity=automation.mock_4_automation,automation.mock_2_automation,automation.mock_0_automation,automation.mock_1_automation"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()

    assert len(json_dict) == 4
    assert json_dict[0]["entity_id"] == "automation.mock_0_automation"
    assert json_dict[1]["entity_id"] == "automation.mock_1_automation"
    assert json_dict[2]["entity_id"] == "automation.mock_2_automation"
    assert json_dict[3]["entity_id"] == "automation.mock_4_automation"

    response = await client.get(
        f"/api/logbook/{end_time.isoformat()}?end_time={end_time}&entity=automation.mock_4_automation,automation.mock_2_automation,automation.mock_0_automation,automation.mock_1_automation"
    )
    assert response.status == HTTPStatus.OK
    json_dict = await response.json()
    assert len(json_dict) == 0
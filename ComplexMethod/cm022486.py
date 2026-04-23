async def test_report_notifications(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test report state works."""
    config = MockConfig(agent_user_ids={"1"})

    assert await async_setup_component(hass, "event", {})
    hass.states.async_set(
        "event.doorbell", "unknown", attributes={"device_class": "doorbell"}
    )

    with (
        patch.object(config, "async_report_state_all", AsyncMock()) as mock_report,
        patch.object(report_state, "INITIAL_REPORT_DELAY", 0),
    ):
        report_state.async_enable_report_state(hass, config)

        async_fire_time_changed(
            hass, datetime.fromisoformat("2023-08-01T00:01:00+00:00")
        )
        await hass.async_block_till_done()

    # Test that enabling report state does a report on event entities
    assert len(mock_report.mock_calls) == 1
    assert mock_report.mock_calls[0][1][0] == {
        "devices": {
            "states": {
                "event.doorbell": {"online": True},
            },
        }
    }

    with patch.object(
        config, "async_report_state", return_value=HTTPStatus(200)
    ) as mock_report_state:
        event_time = datetime.fromisoformat("2023-08-01T00:02:57+00:00")
        epoc_event_time = event_time.timestamp()
        hass.states.async_set(
            "event.doorbell",
            "2023-08-01T00:02:57+00:00",
            attributes={"device_class": "doorbell"},
        )
        async_fire_time_changed(
            hass, datetime.fromisoformat("2023-08-01T00:03:00+00:00")
        )
        await hass.async_block_till_done()

        assert len(mock_report_state.mock_calls) == 1
        notifications_payload = mock_report_state.mock_calls[0][1][0]["devices"][
            "notifications"
        ]["event.doorbell"]
        assert notifications_payload == {
            "ObjectDetection": {
                "objects": {"unclassified": 1},
                "priority": 0,
                "detectionTimestamp": epoc_event_time * 1000,
            }
        }
        assert "Sending event notification for entity event.doorbell" in caplog.text
        assert "Unable to send notification with result code" not in caplog.text

        hass.states.async_set(
            "event.doorbell", "unknown", attributes={"device_class": "doorbell"}
        )
        async_fire_time_changed(
            hass, datetime.fromisoformat("2023-08-01T01:01:00+00:00")
        )
        await hass.async_block_till_done()
        for call in mock_report_state.mock_calls:
            if "states" in call[1][0]["devices"]:
                states = call[1][0]["devices"]["states"]
        assert states["event.doorbell"] == {"online": True}

    # Test the notification request failed
    caplog.clear()
    with patch.object(
        config, "async_report_state", return_value=HTTPStatus(500)
    ) as mock_report_state:
        event_time = datetime.fromisoformat("2023-08-01T01:02:57+00:00")
        epoc_event_time = event_time.timestamp()
        hass.states.async_set(
            "event.doorbell",
            "2023-08-01T01:02:57+00:00",
            attributes={"device_class": "doorbell"},
        )
        async_fire_time_changed(
            hass, datetime.fromisoformat("2023-08-01T01:03:00+00:00")
        )
        await hass.async_block_till_done()
        assert len(mock_report_state.mock_calls) == 1
        for call in mock_report_state.mock_calls:
            if "notifications" in call[1][0]["devices"]:
                notifications = call[1][0]["devices"]["notifications"]
        assert notifications["event.doorbell"] == {
            "ObjectDetection": {
                "objects": {"unclassified": 1},
                "priority": 0,
                "detectionTimestamp": epoc_event_time * 1000,
            }
        }
        assert "Sending event notification for entity event.doorbell" in caplog.text
        assert (
            "Unable to send notification with result code: 500, check log for more info"
            in caplog.text
        )

    # Test disconnecting agent user
    caplog.clear()
    with (
        patch.object(
            config, "async_report_state", return_value=HTTPStatus.NOT_FOUND
        ) as mock_report_state,
        patch.object(config, "async_disconnect_agent_user"),
    ):
        event_time = datetime.fromisoformat("2023-08-01T01:03:57+00:00")
        epoc_event_time = event_time.timestamp()
        hass.states.async_set(
            "event.doorbell",
            "2023-08-01T01:03:57+00:00",
            attributes={"device_class": "doorbell"},
        )
        async_fire_time_changed(
            hass, datetime.fromisoformat("2023-08-01T01:04:00+00:00")
        )
        await hass.async_block_till_done()
        assert len(mock_report_state.mock_calls) == 2
        for call in mock_report_state.mock_calls:
            if "notifications" in call[1][0]["devices"]:
                notifications = call[1][0]["devices"]["notifications"]
            elif "states" in call[1][0]["devices"]:
                states = call[1][0]["devices"]["states"]
        assert notifications["event.doorbell"] == {
            "ObjectDetection": {
                "objects": {"unclassified": 1},
                "priority": 0,
                "detectionTimestamp": epoc_event_time * 1000,
            }
        }
        assert states["event.doorbell"] == {"online": True}
        assert "Sending event notification for entity event.doorbell" in caplog.text
        assert (
            "Unable to send notification with result code: 404, check log for more info"
            in caplog.text
        )
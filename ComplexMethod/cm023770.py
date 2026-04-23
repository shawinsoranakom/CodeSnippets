async def test_timers(hass: HomeAssistant) -> None:
    """Test timer events."""
    assert await async_setup_component(hass, "intent", {})

    with (
        patch(
            "homeassistant.components.wyoming.data.load_wyoming_info",
            return_value=SATELLITE_INFO,
        ),
        patch(
            "homeassistant.components.wyoming.assist_satellite.AsyncTcpClient",
            SatelliteAsyncTcpClient([]),
        ) as mock_client,
    ):
        entry = await setup_config_entry(hass)
        device: SatelliteDevice = entry.runtime_data.device

        async with asyncio.timeout(1):
            await mock_client.connect_event.wait()
            await mock_client.run_satellite_event.wait()

        # Start timer
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_START_TIMER,
            {
                "name": {"value": "test timer"},
                "hours": {"value": 1},
                "minutes": {"value": 2},
                "seconds": {"value": 3},
            },
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_started_event.wait()
            timer_started = mock_client.timer_started
            assert timer_started is not None
            assert timer_started.id
            assert timer_started.name == "test timer"
            assert timer_started.start_hours == 1
            assert timer_started.start_minutes == 2
            assert timer_started.start_seconds == 3
            assert timer_started.total_seconds == (1 * 60 * 60) + (2 * 60) + 3

        # Pause
        mock_client.timer_updated_event.clear()
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_PAUSE_TIMER,
            {},
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_updated_event.wait()
            timer_updated = mock_client.timer_updated
            assert timer_updated is not None
            assert timer_updated.id == timer_started.id
            assert not timer_updated.is_active

        # Resume
        mock_client.timer_updated_event.clear()
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_UNPAUSE_TIMER,
            {},
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_updated_event.wait()
            timer_updated = mock_client.timer_updated
            assert timer_updated is not None
            assert timer_updated.id == timer_started.id
            assert timer_updated.is_active

        # Add time
        mock_client.timer_updated_event.clear()
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_INCREASE_TIMER,
            {
                "hours": {"value": 2},
                "minutes": {"value": 3},
                "seconds": {"value": 4},
            },
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_updated_event.wait()
            timer_updated = mock_client.timer_updated
            assert timer_updated is not None
            assert timer_updated.id == timer_started.id
            assert timer_updated.total_seconds > timer_started.total_seconds

        # Remove time
        mock_client.timer_updated_event.clear()
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_DECREASE_TIMER,
            {
                "hours": {"value": 2},
                "minutes": {"value": 3},
                "seconds": {"value": 5},  # remove 1 extra second
            },
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_updated_event.wait()
            timer_updated = mock_client.timer_updated
            assert timer_updated is not None
            assert timer_updated.id == timer_started.id
            assert timer_updated.total_seconds < timer_started.total_seconds

        # Cancel
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_CANCEL_TIMER,
            {},
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_cancelled_event.wait()
            timer_cancelled = mock_client.timer_cancelled
            assert timer_cancelled is not None
            assert timer_cancelled.id == timer_started.id

        # Start a new timer
        mock_client.timer_started_event.clear()
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_START_TIMER,
            {
                "name": {"value": "test timer"},
                "minutes": {"value": 1},
            },
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_started_event.wait()
            timer_started = mock_client.timer_started
            assert timer_started is not None

        # Finished
        result = await intent_helper.async_handle(
            hass,
            "test",
            intent_helper.INTENT_DECREASE_TIMER,
            {
                "minutes": {"value": 1},  # force finish
            },
            device_id=device.device_id,
        )

        assert result.response_type == intent_helper.IntentResponseType.ACTION_DONE
        async with asyncio.timeout(1):
            await mock_client.timer_finished_event.wait()
            timer_finished = mock_client.timer_finished
            assert timer_finished is not None
            assert timer_finished.id == timer_started.id
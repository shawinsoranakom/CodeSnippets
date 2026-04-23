async def test_setup(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, mock_feed
) -> None:
    """Test the general setup of the platform."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry(
        "1234", "Title 1", 15.5, (-31.0, 150.0), "Category 1"
    )
    mock_entry_2 = _generate_mock_feed_entry(
        "2345", "Title 2", 20.5, (-31.1, 150.1), "Category 1"
    )
    mock_feed.return_value.update.return_value = "OK", [mock_entry_1, mock_entry_2]

    utcnow = dt_util.utcnow()
    freezer.move_to(utcnow)
    with assert_setup_component(1, sensor.DOMAIN):
        assert await async_setup_component(hass, sensor.DOMAIN, VALID_CONFIG)
        # Artificially trigger update.
        hass.bus.fire(EVENT_HOMEASSISTANT_START)
        # Collect events.
        await hass.async_block_till_done()

        all_states = hass.states.async_all()
        assert len(all_states) == 1

        state = hass.states.get("sensor.event_service_any")
        assert state is not None
        assert state.name == "Event Service Any"
        assert int(state.state) == 2
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "Event Service Any",
            ATTR_UNIT_OF_MEASUREMENT: "Events",
            ATTR_ICON: "mdi:alert",
            "Title 1": "16km",
            "Title 2": "20km",
        }

        # Simulate an update - empty data, but successful update,
        # so no changes to entities.
        mock_feed.return_value.update.return_value = "OK_NO_DATA", None
        async_fire_time_changed(hass, utcnow + geo_rss_events.SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

        all_states = hass.states.async_all()
        assert len(all_states) == 1
        state = hass.states.get("sensor.event_service_any")
        assert int(state.state) == 2

        # Simulate an update - empty data, removes all entities
        mock_feed.return_value.update.return_value = "ERROR", None
        async_fire_time_changed(hass, utcnow + 2 * geo_rss_events.SCAN_INTERVAL)
        await hass.async_block_till_done(wait_background_tasks=True)

        all_states = hass.states.async_all()
        assert len(all_states) == 1
        state = hass.states.get("sensor.event_service_any")
        assert int(state.state) == 0
        assert state.attributes == {
            ATTR_FRIENDLY_NAME: "Event Service Any",
            ATTR_UNIT_OF_MEASUREMENT: "Events",
            ATTR_ICON: "mdi:alert",
        }
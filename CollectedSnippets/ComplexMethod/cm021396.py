async def test_setup_imperial(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Test the setup of the integration using imperial unit system."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry(
        "1234",
        "Description 1",
        15.5,
        (38.0, -3.0),
        event_name="Name 1",
        event_type_short="DR",
        event_type="Drought",
    )

    # Patching 'utcnow' to gain more control over the timed update.
    utcnow = dt_util.utcnow()
    with (
        freeze_time(utcnow),
        patch("aio_georss_client.feed.GeoRssFeed.update") as mock_feed_update,
        patch("aio_georss_client.feed.GeoRssFeed.last_timestamp", create=True),
    ):
        mock_feed_update.return_value = "OK", [mock_entry_1]
        config_entry.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            config_entry, data=config_entry.data | CONFIG
        )
        assert await hass.config_entries.async_setup(
            config_entry.entry_id
        )  # Artificially trigger update and collect events.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        assert (
            len(hass.states.async_entity_ids("geo_location"))
            + len(hass.states.async_entity_ids("sensor"))
            == 2
        )

        # Test conversion of 200 miles to kilometers.
        manager = config_entry.runtime_data
        # Ensure that the filter value in km is correctly set.
        assert manager._feed_manager._feed._filter_radius == 321.8688

        state = hass.states.get("geo_location.drought_name_1")
        assert state is not None
        assert state.name == "Drought: Name 1"
        assert state.attributes == {
            ATTR_EXTERNAL_ID: "1234",
            ATTR_LATITUDE: 38.0,
            ATTR_LONGITUDE: -3.0,
            ATTR_FRIENDLY_NAME: "Drought: Name 1",
            ATTR_DESCRIPTION: "Description 1",
            ATTR_EVENT_TYPE: "Drought",
            ATTR_UNIT_OF_MEASUREMENT: "mi",
            ATTR_SOURCE: "gdacs",
            ATTR_ICON: "mdi:water-off",
        }
        # 15.5km (as defined in mock entry) has been converted to 9.6mi.
        assert float(state.state) == 9.6
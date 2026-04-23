async def test_setup_imperial(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the setup of the integration using imperial unit system."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry("1234", "Title 1", 15.5, (38.0, -3.0))

    # Patching 'utcnow' to gain more control over the timed update.
    freezer.move_to(dt_util.utcnow())
    with (
        patch("aio_geojson_client.feed.GeoJsonFeed.update") as mock_feed_update,
        patch("aio_geojson_client.feed.GeoJsonFeed.last_timestamp", create=True),
    ):
        mock_feed_update.return_value = "OK", [mock_entry_1]
        assert await async_setup_component(hass, DOMAIN, CONFIG)
        await hass.async_block_till_done()
        # Artificially trigger update and collect events.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        assert (
            len(hass.states.async_entity_ids("geo_location"))
            + len(hass.states.async_entity_ids("sensor"))
            == 2
        )

        # Test conversion of 200 miles to kilometers.
        manager = hass.config_entries.async_loaded_entries(DOMAIN)[0].runtime_data
        # Ensure that the filter value in km is correctly set.
        assert manager._feed_manager._feed._filter_radius == 321.8688

        state = hass.states.get("geo_location.title_1")
        assert state is not None
        assert state.name == "Title 1"
        assert state.attributes == {
            ATTR_EXTERNAL_ID: "1234",
            ATTR_LATITUDE: 38.0,
            ATTR_LONGITUDE: -3.0,
            ATTR_FRIENDLY_NAME: "Title 1",
            ATTR_UNIT_OF_MEASUREMENT: "mi",
            ATTR_SOURCE: "geonetnz_quakes",
            ATTR_ICON: "mdi:pulse",
        }
        # 15.5km (as defined in mock entry) has been converted to 9.6mi.
        assert float(state.state) == 9.6
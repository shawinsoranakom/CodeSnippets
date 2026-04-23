async def test_setup_imperial(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the setup of the integration using imperial unit system."""
    hass.config.units = US_CUSTOMARY_SYSTEM
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry("1234", "Title 1", 1, 15.5, (38.0, -3.0))

    # Patching 'utcnow' to gain more control over the timed update.
    freezer.move_to(dt_util.utcnow())
    with (
        patch(
            "aio_geojson_client.feed.GeoJsonFeed.update", new_callable=AsyncMock
        ) as mock_feed_update,
        patch("aio_geojson_client.feed.GeoJsonFeed.__init__") as mock_feed_init,
    ):
        mock_feed_update.return_value = "OK", [mock_entry_1]
        assert await async_setup_component(hass, geonetnz_volcano.DOMAIN, CONFIG)
        # Artificially trigger update and collect events.
        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        assert (
            len(hass.states.async_entity_ids("geo_location"))
            + len(hass.states.async_entity_ids("sensor"))
            == 1
        )

        # Test conversion of 200 miles to kilometers.
        assert mock_feed_init.call_args[1].get("filter_radius") == 321.8688

        state = hass.states.get("sensor.volcano_title_1")
        assert state is not None
        assert state.name == "Volcano Title 1"
        assert int(state.state) == 1
        assert state.attributes[ATTR_EXTERNAL_ID] == "1234"
        assert state.attributes[ATTR_LATITUDE] == 38.0
        assert state.attributes[ATTR_LONGITUDE] == -3.0
        assert state.attributes[ATTR_DISTANCE] == 9.6
        assert state.attributes[ATTR_FRIENDLY_NAME] == "Volcano Title 1"
        assert state.attributes[ATTR_UNIT_OF_MEASUREMENT] == "alert level"
        assert state.attributes[ATTR_ICON] == "mdi:image-filter-hdr"
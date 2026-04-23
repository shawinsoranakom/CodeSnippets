async def test_setup(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test the general setup of the platform."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry(
        "1234",
        "Title 1",
        15.5,
        (38.0, -3.0),
        region="Region 1",
        attribution="Attribution 1",
        published=datetime.datetime(2018, 9, 22, 8, 0, tzinfo=datetime.UTC),
        magnitude=5.7,
        image_url="http://image.url/map.jpg",
    )
    mock_entry_2 = _generate_mock_feed_entry(
        "2345", "Title 2", 20.5, (38.1, -3.1), magnitude=4.6
    )
    mock_entry_3 = _generate_mock_feed_entry(
        "3456", "Title 3", 25.5, (38.2, -3.2), region="Region 3"
    )
    mock_entry_4 = _generate_mock_feed_entry("4567", "Title 4", 12.5, (38.3, -3.3))

    utcnow = dt_util.utcnow()
    freezer.move_to(utcnow)

    with patch("georss_client.feed.GeoRssFeed.update") as mock_feed_update:
        mock_feed_update.return_value = (
            "OK",
            [mock_entry_1, mock_entry_2, mock_entry_3],
        )
        with assert_setup_component(1, geo_location.DOMAIN):
            assert await async_setup_component(hass, geo_location.DOMAIN, CONFIG)
            await hass.async_block_till_done()
            # Artificially trigger update.
            hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
            # Collect events.
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            assert len(all_states) == 3

            state = hass.states.get("geo_location.m_5_7_region_1")
            assert state is not None
            assert state.name == "M 5.7 - Region 1"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "1234",
                ATTR_LATITUDE: 38.0,
                ATTR_LONGITUDE: -3.0,
                ATTR_FRIENDLY_NAME: "M 5.7 - Region 1",
                ATTR_TITLE: "Title 1",
                ATTR_REGION: "Region 1",
                ATTR_ATTRIBUTION: "Attribution 1",
                ATTR_PUBLICATION_DATE: datetime.datetime(
                    2018, 9, 22, 8, 0, tzinfo=datetime.UTC
                ),
                ATTR_IMAGE_URL: "http://image.url/map.jpg",
                ATTR_MAGNITUDE: 5.7,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "ign_sismologia",
                ATTR_ICON: "mdi:pulse",
            }
            assert float(state.state) == 15.5

            state = hass.states.get("geo_location.m_4_6")
            assert state is not None
            assert state.name == "M 4.6"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "2345",
                ATTR_LATITUDE: 38.1,
                ATTR_LONGITUDE: -3.1,
                ATTR_FRIENDLY_NAME: "M 4.6",
                ATTR_TITLE: "Title 2",
                ATTR_MAGNITUDE: 4.6,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "ign_sismologia",
                ATTR_ICON: "mdi:pulse",
            }
            assert float(state.state) == 20.5

            state = hass.states.get("geo_location.region_3")
            assert state is not None
            assert state.name == "Region 3"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "3456",
                ATTR_LATITUDE: 38.2,
                ATTR_LONGITUDE: -3.2,
                ATTR_FRIENDLY_NAME: "Region 3",
                ATTR_TITLE: "Title 3",
                ATTR_REGION: "Region 3",
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "ign_sismologia",
                ATTR_ICON: "mdi:pulse",
            }
            assert float(state.state) == 25.5

            # Simulate an update - one existing, one new entry,
            # one outdated entry
            mock_feed_update.return_value = (
                "OK",
                [mock_entry_1, mock_entry_4, mock_entry_3],
            )
            async_fire_time_changed(hass, utcnow + SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            assert len(all_states) == 3

            # Simulate an update - empty data, but successful update,
            # so no changes to entities.
            mock_feed_update.return_value = "OK_NO_DATA", None
            async_fire_time_changed(hass, utcnow + 2 * SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            assert len(all_states) == 3

            # Simulate an update - empty data, removes all entities
            mock_feed_update.return_value = "ERROR", None
            async_fire_time_changed(hass, utcnow + 3 * SCAN_INTERVAL)
            await hass.async_block_till_done(wait_background_tasks=True)

            all_states = hass.states.async_all()
            assert len(all_states) == 0
async def test_setup(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test the general setup of the platform."""
    # Set up some mock feed entries for this test.
    mock_entry_1 = _generate_mock_feed_entry(
        "1234",
        "Title 1",
        15.5,
        (-31.0, 150.0),
        category="Category 1",
        location="Location 1",
        attribution="Attribution 1",
        publication_date=datetime.datetime(2018, 9, 22, 8, 0, tzinfo=datetime.UTC),
        council_area="Council Area 1",
        status="Status 1",
        entry_type="Type 1",
        size="Size 1",
        responsible_agency="Agency 1",
    )
    mock_entry_2 = _generate_mock_feed_entry(
        "2345", "Title 2", 20.5, (-31.1, 150.1), fire=False
    )
    mock_entry_3 = _generate_mock_feed_entry("3456", "Title 3", 25.5, (-31.2, 150.2))
    mock_entry_4 = _generate_mock_feed_entry("4567", "Title 4", 12.5, (-31.3, 150.3))

    utcnow = dt_util.utcnow()
    freezer.move_to(utcnow)

    with patch("aio_geojson_client.feed.GeoJsonFeed.update") as mock_feed_update:
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

            state = hass.states.get("geo_location.title_1")
            assert state is not None
            assert state.name == "Title 1"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "1234",
                ATTR_LATITUDE: -31.0,
                ATTR_LONGITUDE: 150.0,
                ATTR_FRIENDLY_NAME: "Title 1",
                ATTR_CATEGORY: "Category 1",
                ATTR_LOCATION: "Location 1",
                ATTR_ATTRIBUTION: "Attribution 1",
                ATTR_PUBLICATION_DATE: datetime.datetime(
                    2018, 9, 22, 8, 0, tzinfo=datetime.UTC
                ),
                ATTR_FIRE: True,
                ATTR_COUNCIL_AREA: "Council Area 1",
                ATTR_STATUS: "Status 1",
                ATTR_TYPE: "Type 1",
                ATTR_SIZE: "Size 1",
                ATTR_RESPONSIBLE_AGENCY: "Agency 1",
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "nsw_rural_fire_service_feed",
                ATTR_ICON: "mdi:fire",
            }
            assert round(abs(float(state.state) - 15.5), 7) == 0

            state = hass.states.get("geo_location.title_2")
            assert state is not None
            assert state.name == "Title 2"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "2345",
                ATTR_LATITUDE: -31.1,
                ATTR_LONGITUDE: 150.1,
                ATTR_FRIENDLY_NAME: "Title 2",
                ATTR_FIRE: False,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "nsw_rural_fire_service_feed",
                ATTR_ICON: "mdi:alarm-light",
            }
            assert round(abs(float(state.state) - 20.5), 7) == 0

            state = hass.states.get("geo_location.title_3")
            assert state is not None
            assert state.name == "Title 3"
            assert state.attributes == {
                ATTR_EXTERNAL_ID: "3456",
                ATTR_LATITUDE: -31.2,
                ATTR_LONGITUDE: 150.2,
                ATTR_FRIENDLY_NAME: "Title 3",
                ATTR_FIRE: True,
                ATTR_UNIT_OF_MEASUREMENT: UnitOfLength.KILOMETERS,
                ATTR_SOURCE: "nsw_rural_fire_service_feed",
                ATTR_ICON: "mdi:fire",
            }
            assert round(abs(float(state.state) - 25.5), 7) == 0

            # Simulate an update - one existing, one new entry,
            # one outdated entry
            mock_feed_update.return_value = (
                "OK",
                [mock_entry_1, mock_entry_4, mock_entry_3],
            )
            async_fire_time_changed(hass, utcnow + SCAN_INTERVAL)
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            assert len(all_states) == 3

            # Simulate an update - empty data, but successful update,
            # so no changes to entities.
            mock_feed_update.return_value = "OK_NO_DATA", None
            async_fire_time_changed(hass, utcnow + 2 * SCAN_INTERVAL)
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            assert len(all_states) == 3

            # Simulate an update - empty data, removes all entities
            mock_feed_update.return_value = "ERROR", None
            async_fire_time_changed(hass, utcnow + 3 * SCAN_INTERVAL)
            await hass.async_block_till_done()

            all_states = hass.states.async_all()
            assert len(all_states) == 0

            # Artificially trigger update.
            hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
            # Collect events.
            await hass.async_block_till_done()
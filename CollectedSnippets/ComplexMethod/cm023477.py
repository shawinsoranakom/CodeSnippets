async def test_feed_identical_timestamps(
    hass: HomeAssistant, events, feed_identically_timed_events
) -> None:
    """Test feed with 2 entries with identical timestamps."""
    with (
        patch(
            "homeassistant.components.feedreader.coordinator.StoredData.get_timestamp",
            return_value=gmtime(
                datetime.fromisoformat("1970-01-01T00:00:00.0+0000").timestamp()
            ),
        ),
    ):
        assert await async_setup_config_entry(
            hass, VALID_CONFIG_DEFAULT, return_value=feed_identically_timed_events
        )

    assert len(events) == 2
    assert events[0].data.title == "Title 1"
    assert events[1].data.title == "Title 2"
    assert events[0].data.link == "http://www.example.com/link/1"
    assert events[1].data.link == "http://www.example.com/link/2"
    assert events[0].data.id == "GUID 1"
    assert events[1].data.id == "GUID 2"
    assert (
        events[0].data.updated_parsed.tm_year
        == events[1].data.updated_parsed.tm_year
        == 2018
    )
    assert (
        events[0].data.updated_parsed.tm_mon
        == events[1].data.updated_parsed.tm_mon
        == 4
    )
    assert (
        events[0].data.updated_parsed.tm_mday
        == events[1].data.updated_parsed.tm_mday
        == 30
    )
    assert (
        events[0].data.updated_parsed.tm_hour
        == events[1].data.updated_parsed.tm_hour
        == 15
    )
    assert (
        events[0].data.updated_parsed.tm_min
        == events[1].data.updated_parsed.tm_min
        == 10
    )
    assert (
        events[0].data.updated_parsed.tm_sec
        == events[1].data.updated_parsed.tm_sec
        == 0
    )
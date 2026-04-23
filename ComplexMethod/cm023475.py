async def test_feed(hass: HomeAssistant, events, feed_one_event) -> None:
    """Test simple rss feed with valid data."""
    assert await async_setup_config_entry(
        hass, VALID_CONFIG_DEFAULT, return_value=feed_one_event
    )

    assert len(events) == 1
    assert events[0].data.title == "Title 1"
    assert events[0].data.description == "Description 1"
    assert events[0].data.link == "http://www.example.com/link/1"
    assert events[0].data.id == "GUID 1"
    assert events[0].data.published_parsed.tm_year == 2018
    assert events[0].data.published_parsed.tm_mon == 4
    assert events[0].data.published_parsed.tm_mday == 30
    assert events[0].data.published_parsed.tm_hour == 5
    assert events[0].data.published_parsed.tm_min == 10
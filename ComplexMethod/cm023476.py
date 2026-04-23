async def test_atom_feed(hass: HomeAssistant, events, feed_atom_event) -> None:
    """Test simple atom feed with valid data."""
    assert await async_setup_config_entry(
        hass, VALID_CONFIG_DEFAULT, return_value=feed_atom_event
    )

    assert len(events) == 1
    assert events[0].data.title == "Atom-Powered Robots Run Amok"
    assert events[0].data.description == "Some text."
    assert events[0].data.link == "http://example.org/2003/12/13/atom03"
    assert events[0].data.id == "urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a"
    assert events[0].data.updated_parsed.tm_year == 2003
    assert events[0].data.updated_parsed.tm_mon == 12
    assert events[0].data.updated_parsed.tm_mday == 13
    assert events[0].data.updated_parsed.tm_hour == 18
    assert events[0].data.updated_parsed.tm_min == 30
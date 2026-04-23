async def test_reconfigure_errors(
    hass: HomeAssistant, feedparser, setup_entry, feed_one_event
) -> None:
    """Test starting a reconfigure flow by user which results in an URL error."""
    entry = create_mock_entry(VALID_CONFIG_DEFAULT)
    entry.add_to_hass(hass)

    # init user flow
    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    # raise URLError
    feedparser.side_effect = urllib.error.URLError("Test")
    feedparser.return_value = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "http://other.rss.local/rss_feed.xml",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"
    assert result["errors"] == {"base": "url_error"}

    # success
    feedparser.side_effect = None
    feedparser.return_value = feed_one_event

    # success
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_URL: "http://other.rss.local/rss_feed.xml",
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert entry.data == {
        CONF_URL: "http://other.rss.local/rss_feed.xml",
    }
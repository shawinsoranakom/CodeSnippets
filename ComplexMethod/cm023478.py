async def test_user_errors(
    hass: HomeAssistant, feedparser, setup_entry, feed_one_event
) -> None:
    """Test starting a flow by user which results in an URL error."""
    # init user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # raise URLError
    feedparser.side_effect = urllib.error.URLError("Test")
    feedparser.return_value = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: URL}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "url_error"}

    # success
    feedparser.side_effect = None
    feedparser.return_value = feed_one_event
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_URL: URL}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == FEED_TITLE
    assert result["data"][CONF_URL] == URL
    assert result["options"][CONF_MAX_ENTRIES] == DEFAULT_MAX_ENTRIES
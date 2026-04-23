async def test_single_closed_site_no_closed_date(
    hass: HomeAssistant, single_site_closed_no_close_date_api: Mock
) -> None:
    """Test single closed site with no closed date."""
    initial_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert initial_result.get("type") is FlowResultType.FORM
    assert initial_result.get("step_id") == "user"

    # Test filling in API key
    enter_api_key_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_API_TOKEN: API_KEY},
    )
    assert enter_api_key_result.get("type") is FlowResultType.FORM
    assert enter_api_key_result.get("step_id") == "site"

    select_site_result = await hass.config_entries.flow.async_configure(
        enter_api_key_result["flow_id"],
        {CONF_SITE_ID: "01FG0AGP818PXK0DWHXJRRT2DH", CONF_SITE_NAME: "Home"},
    )

    # Show available sites
    assert select_site_result.get("type") is FlowResultType.CREATE_ENTRY
    assert select_site_result.get("title") == "Home"
    data = select_site_result.get("data")
    assert data
    assert data[CONF_API_TOKEN] == API_KEY
    assert data[CONF_SITE_ID] == "01FG0AGP818PXK0DWHXJRRT2DH"
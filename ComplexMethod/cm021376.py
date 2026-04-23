async def test_fetch_general_and_feed_in_site(
    hass: HomeAssistant, current_price_api: Mock
) -> None:
    """Test fetching a site with a general and feed_in channel."""

    current_price_api.get_current_prices.return_value = (
        GENERAL_CHANNEL + FEED_IN_CHANNEL
    )
    data_service = AmberUpdateCoordinator(
        hass, MOCKED_ENTRY, current_price_api, GENERAL_AND_FEED_IN_SITE_ID
    )
    result = await data_service._async_update_data()

    current_price_api.get_current_prices.assert_called_with(
        GENERAL_AND_FEED_IN_SITE_ID,
        next=288,
        _request_timeout=REQUEST_TIMEOUT,
    )

    assert result["current"].get("general") == GENERAL_CHANNEL[0].actual_instance
    assert result["forecasts"].get("general") == [
        GENERAL_CHANNEL[1].actual_instance,
        GENERAL_CHANNEL[2].actual_instance,
        GENERAL_CHANNEL[3].actual_instance,
    ]
    assert result["current"].get("controlled_load") is None
    assert result["forecasts"].get("controlled_load") is None
    assert result["current"].get("feed_in") is FEED_IN_CHANNEL[0].actual_instance
    assert result["forecasts"].get("feed_in") == [
        FEED_IN_CHANNEL[1].actual_instance,
        FEED_IN_CHANNEL[2].actual_instance,
        FEED_IN_CHANNEL[3].actual_instance,
    ]
    assert result["grid"]["renewables"] == round(
        GENERAL_CHANNEL[0].actual_instance.renewables
    )
    assert result["grid"]["price_spike"] == "none"
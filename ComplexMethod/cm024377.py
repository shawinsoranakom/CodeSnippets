async def test_sensor(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test that sensor has a value."""
    with (
        patch(
            "pykrakenapi.KrakenAPI.get_tradable_asset_pairs",
            return_value=TRADEABLE_ASSET_PAIR_RESPONSE,
        ),
        patch(
            "pykrakenapi.KrakenAPI.get_ticker_information",
            return_value=TICKER_INFORMATION_RESPONSE,
        ),
    ):
        entry = MockConfigEntry(
            domain=DOMAIN,
            unique_id="0123456789",
            options={
                CONF_SCAN_INTERVAL: DEFAULT_SCAN_INTERVAL,
                CONF_TRACKED_ASSET_PAIRS: [
                    "ADA/XBT",
                    "ADA/ETH",
                    "XBT/EUR",
                    "XBT/GBP",
                    "XBT/USD",
                    "XBT/JPY",
                ],
            },
        )
        entry.add_to_hass(hass)

        await hass.config_entries.async_setup(entry.entry_id)

        await hass.async_block_till_done()

        hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()

        xbt_usd_sensor = hass.states.get("sensor.xbt_usd_ask")
        assert xbt_usd_sensor.state == "0.0003494"
        assert xbt_usd_sensor.attributes["icon"] == "mdi:currency-usd"

        xbt_eur_sensor = hass.states.get("sensor.xbt_eur_ask")
        assert xbt_eur_sensor.state == "0.0003494"
        assert xbt_eur_sensor.attributes["icon"] == "mdi:currency-eur"

        ada_xbt_sensor = hass.states.get("sensor.ada_xbt_ask")
        assert ada_xbt_sensor.state == "0.0003494"
        assert ada_xbt_sensor.attributes["icon"] == "mdi:currency-btc"

        xbt_jpy_sensor = hass.states.get("sensor.xbt_jpy_ask")
        assert xbt_jpy_sensor.state == "0.0003494"
        assert xbt_jpy_sensor.attributes["icon"] == "mdi:currency-jpy"

        xbt_gbp_sensor = hass.states.get("sensor.xbt_gbp_ask")
        assert xbt_gbp_sensor.state == "0.0003494"
        assert xbt_gbp_sensor.attributes["icon"] == "mdi:currency-gbp"

        ada_eth_sensor = hass.states.get("sensor.ada_eth_ask")
        assert ada_eth_sensor.state == "0.0003494"
        assert ada_eth_sensor.attributes["icon"] == "mdi:cash"

        xbt_usd_ask_volume = hass.states.get("sensor.xbt_usd_ask_volume")
        assert xbt_usd_ask_volume.state == "15949"

        xbt_usd_last_trade_closed = hass.states.get("sensor.xbt_usd_last_trade_closed")
        assert xbt_usd_last_trade_closed.state == "0.0003478"

        xbt_usd_bid_volume = hass.states.get("sensor.xbt_usd_bid_volume")
        assert xbt_usd_bid_volume.state == "20792"

        xbt_usd_volume_today = hass.states.get("sensor.xbt_usd_volume_today")
        assert xbt_usd_volume_today.state == "146300.24906838"

        xbt_usd_volume_last_24h = hass.states.get("sensor.xbt_usd_volume_last_24h")
        assert xbt_usd_volume_last_24h.state == "253478.04715403"

        xbt_usd_volume_weighted_average_today = hass.states.get(
            "sensor.xbt_usd_volume_weighted_average_today"
        )
        assert xbt_usd_volume_weighted_average_today.state == "0.000348573"

        xbt_usd_volume_weighted_average_last_24h = hass.states.get(
            "sensor.xbt_usd_volume_weighted_average_last_24h"
        )
        assert xbt_usd_volume_weighted_average_last_24h.state == "0.000344881"

        xbt_usd_number_of_trades_today = hass.states.get(
            "sensor.xbt_usd_number_of_trades_today"
        )
        assert xbt_usd_number_of_trades_today.state == "82"

        xbt_usd_number_of_trades_last_24h = hass.states.get(
            "sensor.xbt_usd_number_of_trades_last_24h"
        )
        assert xbt_usd_number_of_trades_last_24h.state == "128"

        xbt_usd_low_last_24h = hass.states.get("sensor.xbt_usd_low_last_24h")
        assert xbt_usd_low_last_24h.state == "0.0003446"

        xbt_usd_high_last_24h = hass.states.get("sensor.xbt_usd_high_last_24h")
        assert xbt_usd_high_last_24h.state == "0.0003521"

        xbt_usd_opening_price_today = hass.states.get(
            "sensor.xbt_usd_opening_price_today"
        )
        assert xbt_usd_opening_price_today.state == "0.0003513"
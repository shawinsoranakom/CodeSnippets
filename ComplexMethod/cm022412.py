async def test_websocket_core_update(hass: HomeAssistant, client) -> None:
    """Test core config update websocket command."""
    assert hass.config.latitude != 60
    assert hass.config.longitude != 50
    assert hass.config.elevation != 25
    assert hass.config.location_name != "Huis"
    assert hass.config.units is not US_CUSTOMARY_SYSTEM
    assert hass.config.time_zone != "America/New_York"
    assert hass.config.external_url != "https://www.example.com"
    assert hass.config.internal_url != "http://example.com"
    assert hass.config.currency == "EUR"
    assert hass.config.country != "SE"
    assert hass.config.language != "sv"
    assert hass.config.radius != 150

    with (
        patch("homeassistant.util.dt.set_default_time_zone") as mock_set_tz,
        patch(
            "homeassistant.components.config.core.async_update_suggested_units"
        ) as mock_update_sensor_units,
    ):
        await client.send_json(
            {
                "id": 5,
                "type": "config/core/update",
                "latitude": 60,
                "longitude": 50,
                "elevation": 25,
                "location_name": "Huis",
                "unit_system": "imperial",
                "time_zone": "America/New_York",
                "external_url": "https://www.example.com",
                "internal_url": "http://example.local",
                "currency": "USD",
                "country": "SE",
                "language": "sv",
                "radius": 150,
            }
        )

        msg = await client.receive_json()

        mock_update_sensor_units.assert_not_called()

    assert msg["id"] == 5
    assert msg["type"] == TYPE_RESULT
    assert msg["success"]
    assert hass.config.latitude == 60
    assert hass.config.longitude == 50
    assert hass.config.elevation == 25
    assert hass.config.location_name == "Huis"
    assert hass.config.units is US_CUSTOMARY_SYSTEM
    assert hass.config.external_url == "https://www.example.com"
    assert hass.config.internal_url == "http://example.local"
    assert hass.config.currency == "USD"
    assert hass.config.country == "SE"
    assert hass.config.language == "sv"
    assert hass.config.radius == 150

    assert len(mock_set_tz.mock_calls) == 1
    assert mock_set_tz.mock_calls[0][1][0] == dt_util.get_time_zone("America/New_York")

    with (
        patch("homeassistant.util.dt.set_default_time_zone") as mock_set_tz,
        patch(
            "homeassistant.components.config.core.async_update_suggested_units"
        ) as mock_update_sensor_units,
    ):
        await client.send_json(
            {
                "id": 6,
                "type": "config/core/update",
                "unit_system": "metric",
                "update_units": True,
            }
        )

        msg = await client.receive_json()

        mock_update_sensor_units.assert_called_once()
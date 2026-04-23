async def test_coordinator_multi_plane_initialization(
    hass: HomeAssistant,
    mock_forecast_solar: MagicMock,
) -> None:
    """Test the Forecast.Solar coordinator multi-plane initialization."""
    options = {
        CONF_API_KEY: "abcdef1234567890",
        CONF_DAMPING_MORNING: 0.5,
        CONF_DAMPING_EVENING: 0.5,
        CONF_INVERTER_SIZE: 2000,
    }

    mock_config_entry = MockConfigEntry(
        title="Green House",
        unique_id="unique",
        version=3,
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
        },
        options=options,
        subentries_data=[
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 30,
                    CONF_AZIMUTH: 190,
                    CONF_MODULES_POWER: 5100,
                },
                subentry_id="plane_1",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="30° / 190° / 5100W",
                unique_id=None,
            ),
            ConfigSubentryData(
                data={
                    CONF_DECLINATION: 45,
                    CONF_AZIMUTH: 270,
                    CONF_MODULES_POWER: 3000,
                },
                subentry_id="plane_2",
                subentry_type=SUBENTRY_TYPE_PLANE,
                title="45° / 270° / 3000W",
                unique_id=None,
            ),
        ],
    )

    mock_config_entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.forecast_solar.coordinator.ForecastSolar",
        return_value=mock_forecast_solar,
    ) as forecast_solar_mock:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    forecast_solar_mock.assert_called_once()
    _, kwargs = forecast_solar_mock.call_args

    assert kwargs["latitude"] == 52.42
    assert kwargs["longitude"] == 4.42
    assert kwargs["api_key"] == "abcdef1234567890"

    # Main plane (plane_1)
    assert kwargs["declination"] == 30
    assert kwargs["azimuth"] == 10  # 190 - 180
    assert kwargs["kwp"] == 5.1  # 5100 / 1000

    # Additional planes (plane_2)
    planes = kwargs["planes"]
    assert len(planes) == 1
    assert isinstance(planes[0], Plane)
    assert planes[0].declination == 45
    assert planes[0].azimuth == 90  # 270 - 180
    assert planes[0].kwp == 3.0
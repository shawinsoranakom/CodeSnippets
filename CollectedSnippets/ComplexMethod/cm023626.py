async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_fire_client: MagicMock,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test re-configuration flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        unique_id="57.2898-13.6304",
        data={"location": {"latitude": 57.2898, "longitude": 13.6304}},
        version=3,
    )
    entry.add_to_hass(hass)

    entity = entity_registry.async_get_or_create(
        WEATHER_DOMAIN, DOMAIN, "57.2898, 13.6304"
    )
    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "57.2898, 13.6304")},
        manufacturer="SMHI",
        model="v2",
        name=entry.title,
    )

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM

    mock_client.async_get_daily_forecast.side_effect = SmhiForecastException

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: {
                CONF_LATITUDE: 0.0,
                CONF_LONGITUDE: 0.0,
            }
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "wrong_location"}

    mock_client.async_get_daily_forecast.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: {
                CONF_LATITUDE: 58.2898,
                CONF_LONGITUDE: 14.6304,
            }
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    entry = hass.config_entries.async_get_entry(entry.entry_id)
    assert entry.title == "Home"
    assert entry.unique_id == "58.2898-14.6304"
    assert entry.data == {
        "location": {
            "latitude": 58.2898,
            "longitude": 14.6304,
        },
    }
    entity = entity_registry.async_get(entity.entity_id)
    assert entity
    assert entity.unique_id == "58.2898, 14.6304"
    device = device_registry.async_get(device.id)
    assert device
    assert device.identifiers == {(DOMAIN, "58.2898, 14.6304")}
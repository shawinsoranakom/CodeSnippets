async def test_form(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_fire_client: MagicMock,
) -> None:
    """Test we get the form and create an entry."""

    hass.config.latitude = 0.0
    hass.config.longitude = 0.0

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.smhi.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_LOCATION: {
                    CONF_LATITUDE: 0.0,
                    CONF_LONGITUDE: 0.0,
                }
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert result["result"].unique_id == "0.0-0.0"
    assert result["data"] == {
        "location": {
            "latitude": 0.0,
            "longitude": 0.0,
        },
    }
    assert len(mock_setup_entry.mock_calls) == 1

    # Check title is "Weather" when not home coordinates
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_LOCATION: {
                CONF_LATITUDE: 1.0,
                CONF_LONGITUDE: 1.0,
            }
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Weather 1.0 1.0"
    assert result["data"] == {
        "location": {
            "latitude": 1.0,
            "longitude": 1.0,
        },
    }
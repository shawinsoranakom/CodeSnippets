async def test_user(hass: HomeAssistant) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.tankerkoenig.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig.nearby_stations",
            return_value=NEARBY_STATIONS,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "select_station"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_STATIONS_DATA
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_NAME] == "Home"
        assert result["data"][CONF_API_KEY] == "269534f6-xxxx-xxxx-xxxx-yyyyzzzzxxxx"
        assert result["data"][CONF_LOCATION] == {"latitude": 51.0, "longitude": 13.0}
        assert result["data"][CONF_RADIUS] == 2.0
        assert result["data"][CONF_STATIONS] == [
            "3bcd61da-xxxx-xxxx-xxxx-19d5523a7ae8",
            "36b4b812-xxxx-xxxx-xxxx-c51735325858",
        ]
        assert result["options"][CONF_SHOW_ON_MAP]

        await hass.async_block_till_done()

    assert mock_setup_entry.called
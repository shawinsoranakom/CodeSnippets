async def test_user(hass: HomeAssistant) -> None:
    """Test starting a flow by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.pegel_online.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.pegel_online.config_flow.PegelOnline",
        ) as pegelonline,
    ):
        pegelonline.return_value = PegelOnlineMock(nearby_stations=MOCK_NEARBY_STATIONS)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP1
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "select_station"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA_STEP2
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_STATION] == "70272185-xxxx-xxxx-xxxx-43bea330dcae"
        assert result["title"] == "DRESDEN ELBE"

        await hass.async_block_till_done()

    assert mock_setup_entry.called
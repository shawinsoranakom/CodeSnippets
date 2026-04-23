async def test_user_list(hass: HomeAssistant, client_multiple) -> None:
    """Test user config."""

    # test with all provided with search returning more than 1 place
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_2_NAME},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cities"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_CITY: f"{CITY_3};{CITY_3_LAT};{CITY_3_LON}"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_3_LAT}, {CITY_3_LON}"
    assert result["title"] == f"{CITY_3}"
    assert result["data"][CONF_LATITUDE] == str(CITY_3_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_3_LON)
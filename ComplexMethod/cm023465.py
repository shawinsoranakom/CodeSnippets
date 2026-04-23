async def test_user(hass: HomeAssistant, client_single) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # test with all provided with search returning only 1 place
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_CITY: CITY_1_POSTAL},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == f"{CITY_1_LAT}, {CITY_1_LON}"
    assert result["title"] == f"{CITY_1}"
    assert result["data"][CONF_LATITUDE] == str(CITY_1_LAT)
    assert result["data"][CONF_LONGITUDE] == str(CITY_1_LON)
async def test_user(hass: HomeAssistant, mock_rova: MagicMock) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    # test with all information provided
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_ZIP_CODE: ZIP_CODE,
            CONF_HOUSE_NUMBER: HOUSE_NUMBER,
            CONF_HOUSE_NUMBER_SUFFIX: HOUSE_NUMBER_SUFFIX,
        },
    )
    assert result.get("type") is FlowResultType.CREATE_ENTRY

    data = result.get("data")
    assert data
    assert data[CONF_ZIP_CODE] == ZIP_CODE
    assert data[CONF_HOUSE_NUMBER] == HOUSE_NUMBER
    assert data[CONF_HOUSE_NUMBER_SUFFIX] == HOUSE_NUMBER_SUFFIX
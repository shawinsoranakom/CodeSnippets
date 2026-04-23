async def test_create_entry(
    hass: HomeAssistant,
    client,
    errors,
    get_client_with_exception,
    mock_aionotion,
) -> None:
    """Test creating an etry (including recovery from errors)."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test errors that can arise when getting a Notion API client:
    with patch(
        "homeassistant.components.notion.config_flow.async_get_client_with_credentials",
        get_client_with_exception,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_USERNAME: TEST_USERNAME,
                CONF_PASSWORD: TEST_PASSWORD,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == errors

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USERNAME: TEST_USERNAME,
            CONF_PASSWORD: TEST_PASSWORD,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_USERNAME
    assert result["data"] == {
        CONF_REFRESH_TOKEN: TEST_REFRESH_TOKEN,
        CONF_USERNAME: TEST_USERNAME,
        CONF_USER_UUID: TEST_USER_UUID,
    }
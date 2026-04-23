async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_setup_entry,
) -> None:
    """Check full of adding a single heat pump."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )

    await handle_oauth(hass, hass_client_no_auth, aioclient_mock, result)

    with (
        patch(
            "homeassistant.components.weheat.config_flow.async_get_user_id_from_token",
            return_value=USER_UUID_1,
        ) as mock_weheat,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_weheat.mock_calls) == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == USER_UUID_1
    assert result["result"].title == ENTRY_TITLE
    assert result["data"][CONF_TOKEN][CONF_REFRESH_TOKEN] == MOCK_REFRESH_TOKEN
    assert result["data"][CONF_TOKEN][CONF_ACCESS_TOKEN] == MOCK_ACCESS_TOKEN
    assert result["data"][CONF_AUTH_IMPLEMENTATION] == DOMAIN
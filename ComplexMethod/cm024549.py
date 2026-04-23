async def test_config_flow_multiple_accounts(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test what happens if multiple Kamereon accounts are available."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    renault_account_1 = RenaultAccount(
        "account_id_1",
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    renault_account_2 = RenaultAccount(
        "account_id_2",
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    renault_vehicles = schemas.KamereonVehiclesResponseSchema.loads(
        await async_load_fixture(hass, "renault/vehicle_zoe_40.json")
    )

    # Multiple accounts
    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account_1, renault_account_2],
        ),
        patch(
            "renault_api.renault_account.RenaultAccount.get_vehicles",
            return_value=renault_vehicles,
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_LOCALE: "fr_FR",
                CONF_USERNAME: "email@test.com",
                CONF_PASSWORD: "test",
            },
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "kamereon"

    # Account selected
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_KAMEREON_ACCOUNT_ID: "account_id_2"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "account_id_2"
    assert result["data"][CONF_USERNAME] == "email@test.com"
    assert result["data"][CONF_PASSWORD] == "test"
    assert result["data"][CONF_KAMEREON_ACCOUNT_ID] == "account_id_2"
    assert result["data"][CONF_LOCALE] == "fr_FR"
    assert result["context"]["unique_id"] == "account_id_2"

    assert len(mock_setup_entry.mock_calls) == 1
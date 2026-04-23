async def test_config_flow_single_account(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    exception: Exception | type[Exception],
    error: str,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    # Raise error
    with patch(
        "renault_api.renault_session.RenaultSession.login",
        side_effect=exception,
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
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": error}

    data_schema = result["data_schema"].schema
    assert get_schema_suggested_value(data_schema, CONF_LOCALE) == "fr_FR"
    assert get_schema_suggested_value(data_schema, CONF_USERNAME) == "email@test.com"
    assert get_schema_suggested_value(data_schema, CONF_PASSWORD) == "test"

    renault_account = AsyncMock()
    type(renault_account).account_id = PropertyMock(return_value="account_id_1")
    renault_account.get_vehicles.return_value = (
        schemas.KamereonVehiclesResponseSchema.loads(
            await async_load_fixture(hass, "vehicle_zoe_40.json", DOMAIN)
        )
    )

    # Account list single
    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_account.RenaultAccount.account_id", return_value="123"
        ),
        patch(
            "renault_api.renault_client.RenaultClient.get_api_accounts",
            return_value=[renault_account],
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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "account_id_1"
    assert result["data"][CONF_USERNAME] == "email@test.com"
    assert result["data"][CONF_PASSWORD] == "test"
    assert result["data"][CONF_KAMEREON_ACCOUNT_ID] == "account_id_1"
    assert result["data"][CONF_LOCALE] == "fr_FR"
    assert result["context"]["unique_id"] == "account_id_1"

    assert len(mock_setup_entry.mock_calls) == 1
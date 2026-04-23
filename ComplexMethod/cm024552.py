async def test_reconfigure_mismatch(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure fails on account ID mismatch."""
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    data_schema = result["data_schema"].schema
    assert get_schema_suggested_value(data_schema, CONF_LOCALE) == "fr_FR"
    assert get_schema_suggested_value(data_schema, CONF_USERNAME) == "email@test.com"
    assert get_schema_suggested_value(data_schema, CONF_PASSWORD) == "test"

    renault_account = AsyncMock()
    type(renault_account).account_id = PropertyMock(return_value="account_id_other")
    renault_account.get_vehicles.return_value = (
        schemas.KamereonVehiclesResponseSchema.loads(
            await async_load_fixture(hass, "vehicle_zoe_40.json", DOMAIN)
        )
    )

    # Account list single
    with (
        patch("renault_api.renault_session.RenaultSession.login"),
        patch(
            "renault_api.renault_account.RenaultAccount.account_id", return_value="1234"
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
                CONF_USERNAME: "email2@test.com",
                CONF_PASSWORD: "test2",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "unique_id_mismatch"

    # Unchanged values
    assert config_entry.data[CONF_USERNAME] == "email@test.com"
    assert config_entry.data[CONF_PASSWORD] == "test"
    assert config_entry.data[CONF_KAMEREON_ACCOUNT_ID] == "account_id_1"
    assert config_entry.data[CONF_LOCALE] == "fr_FR"

    assert len(mock_setup_entry.mock_calls) == 0
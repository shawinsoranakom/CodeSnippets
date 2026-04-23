async def test_flow_reconfigure_success(
    hass: HomeAssistant,
    cookidoo_config_entry: AsyncMock,
    mock_cookidoo_client: AsyncMock,
) -> None:
    """Test we get the reconfigure flow and create entry with success."""
    cookidoo_config_entry.add_to_hass(hass)
    await setup_integration(hass, cookidoo_config_entry)

    result = await cookidoo_config_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["handler"] == "cookidoo"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            **MOCK_DATA_USER_STEP,
            CONF_EMAIL: "new-email",
            CONF_PASSWORD: "new-password",
            CONF_COUNTRY: "DE",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "language"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_LANGUAGE: "de-DE"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert cookidoo_config_entry.data == {
        **MOCK_DATA_USER_STEP,
        CONF_EMAIL: "new-email",
        CONF_PASSWORD: "new-password",
        CONF_COUNTRY: "DE",
        CONF_LANGUAGE: "de-DE",
    }
    assert len(hass.config_entries.async_entries()) == 1
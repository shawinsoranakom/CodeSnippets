async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test the reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=TEST_USER_EMAIL,
        data={CONF_API_KEY: SUBSCRIPTION_KEY},
    )
    mock_config.add_to_hass(hass)

    with patch(
        "homeassistant.components.osoenergy.config_flow.OSOEnergy.get_user_email",
        return_value=None,
    ):
        result = await mock_config.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    with patch(
        "homeassistant.components.osoenergy.config_flow.OSOEnergy.get_user_email",
        return_value=TEST_USER_EMAIL,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: SUBSCRIPTION_KEY,
            },
        )
    await hass.async_block_till_done()

    assert mock_config.data.get(CONF_API_KEY) == SUBSCRIPTION_KEY
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
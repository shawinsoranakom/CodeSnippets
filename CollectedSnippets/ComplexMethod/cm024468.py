async def test_reauth_flow(hass: HomeAssistant) -> None:
    """Test reauth works."""
    mock_config = MockConfigEntry(
        domain=DOMAIN, unique_id=UNIQUE_ID, data=FIXTURE_USER_INPUT
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {"base": "authorization_error"}

    with (
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.authenticate",
            return_value=True,
        ),
        patch(
            "homeassistant.components.ovo_energy.config_flow.OVOEnergy.username",
            return_value=FIXTURE_USER_INPUT[CONF_USERNAME],
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            FIXTURE_REAUTH_INPUT,
        )
        await hass.async_block_till_done()

        assert result2["type"] is FlowResultType.ABORT
        assert result2["reason"] == "reauth_successful"
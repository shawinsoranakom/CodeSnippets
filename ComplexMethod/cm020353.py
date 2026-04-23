async def test_flow_user_with_api_key_v6(hass: HomeAssistant) -> None:
    """Test user initialized flow with api key needed."""
    mocked_hole = _create_mocked_hole(has_data=False, api_version=6)
    with (
        _patch_init_hole(mocked_hole),
        _patch_config_flow_hole(mocked_hole),
        _patch_setup_hole() as mock_setup,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={**CONFIG_FLOW_USER, CONF_API_KEY: "invalid_password"},
        )
        # we have had no response from the server yet, so we expect an error
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}

        # now we have a valid passiword
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG_FLOW_USER,
        )

        # form should be complete with a valid config entry
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == CONFIG_ENTRY_WITH_API_KEY
        mock_setup.assert_called_once()

        # duplicated server
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_FLOW_USER,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"
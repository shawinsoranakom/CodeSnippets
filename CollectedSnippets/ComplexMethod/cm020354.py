async def test_flow_user_with_api_key_v5(hass: HomeAssistant) -> None:
    """Test user initialized flow with api key needed."""
    mocked_hole = _create_mocked_hole(api_version=5)
    with (
        _patch_init_hole(mocked_hole),
        _patch_config_flow_hole(mocked_hole),
        _patch_setup_hole() as mock_setup,
    ):
        # start the flow as a user initiated flow
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        # configure the flow with an invalid api key
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={**CONFIG_FLOW_USER, CONF_API_KEY: "wrong_token"},
        )

        # confirm an invalid authentication error
        assert result["errors"] == {CONF_API_KEY: "invalid_auth"}

        # configure the flow with a valid api key
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONFIG_FLOW_USER,
        )

        # in API V5 we get data to confirm authentication
        assert mocked_hole.instances[-1].data == ZERO_DATA

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == NAME
        assert result["data"] == {**CONFIG_ENTRY_WITH_API_KEY}
        mock_setup.assert_called_once()

        # duplicated server
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data=CONFIG_FLOW_USER,
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "already_configured"
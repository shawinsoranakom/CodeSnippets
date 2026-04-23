async def test_flow_reauth(hass: HomeAssistant) -> None:
    """Test reauth flow."""
    mocked_hole = _create_mocked_hole(has_data=False, api_version=5)
    entry = MockConfigEntry(
        domain=pi_hole.DOMAIN,
        data={**CONFIG_DATA_DEFAULTS, CONF_API_KEY: "oldkey"},
    )
    entry.add_to_hass(hass)
    with _patch_init_hole(mocked_hole), _patch_config_flow_hole(mocked_hole):
        assert not await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        flows = hass.config_entries.flow.async_progress()

        assert len(flows) == 1
        assert flows[0]["step_id"] == "reauth_confirm"
        assert flows[0]["context"]["entry_id"] == entry.entry_id
        mocked_hole.instances[-1].api_token = "newkey"
        result = await hass.config_entries.flow.async_configure(
            flows[0]["flow_id"],
            user_input={CONF_API_KEY: "newkey"},
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.data[CONF_API_KEY] == "newkey"
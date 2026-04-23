async def test_flow_reconfigure_token(
    hass: HomeAssistant,
    entry_data: dict[str, Any],
    step_id: str,
) -> None:
    """Test reconfigure flow with access token."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            **entry_data,
        },
    )

    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == step_id

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TOKEN: "access_token"},
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_USERNAME] == "username"
    assert config_entry.data[CONF_TOKEN] == "access_token"

    assert len(hass.config_entries.async_entries()) == 1
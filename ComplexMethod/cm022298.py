async def test_manual_setup(hass: HomeAssistant) -> None:
    """Test manually setting up."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert not result["errors"]

    with (
        _patch_get_info(),
        patch(f"{MODULE}.async_setup_entry", return_value=True) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: IP_ADDRESS}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_HOST: IP_ADDRESS}
    assert result["title"] == DEFAULT_ENTRY_TITLE
    assert len(mock_setup_entry.mock_calls) == 1
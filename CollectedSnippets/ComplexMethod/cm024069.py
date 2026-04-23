async def test_form(hass: HomeAssistant) -> None:
    """Test flow when configuring URL only."""
    # Pretend we already set up a config entry.
    hass.config.components.add(DOMAIN)
    MockConfigEntry(
        domain=DOMAIN,
        state=config_entries.ConfigEntryState.LOADED,
    ).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with (
        patch(
            "homeassistant.components.ollama.config_flow.ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch(
            "homeassistant.components.ollama.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {ollama.CONF_URL: "http://localhost:11434"}
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["data"] == {ollama.CONF_URL: "http://localhost:11434"}

    # No subentries created by default
    assert len(result2.get("subentries", [])) == 0
    assert len(mock_setup_entry.mock_calls) == 1
    assert CONF_API_KEY not in result2["data"]
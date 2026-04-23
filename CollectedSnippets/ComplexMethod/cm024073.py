async def test_subentry_reconfigure_with_download(
    hass: HomeAssistant,
    mock_init_component,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfiguring subentry when model needs to be downloaded."""
    subentry = next(iter(mock_config_entry.subentries.values()))

    async def delayed_pull(self, model: str) -> None:
        """Simulate a delayed model download."""
        assert model == "llama3.2:latest"
        await asyncio.sleep(0)  # yield the event loop

    with (
        patch(
            "ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch("ollama.AsyncClient.pull", delayed_pull),
    ):
        reconfigure_flow = await mock_config_entry.start_subentry_reconfigure_flow(
            hass, subentry.subentry_id
        )

        assert reconfigure_flow["type"] is FlowResultType.FORM
        assert reconfigure_flow["step_id"] == "set_options"

        # Reconfigure with a model that needs downloading
        result = await hass.config_entries.subentries.async_configure(
            reconfigure_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",
                ollama.CONF_PROMPT: "updated prompt",
                ollama.CONF_MAX_HISTORY: 75,
                ollama.CONF_NUM_CTX: 8192,
                ollama.CONF_THINK: True,
            },
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "download"

        await hass.async_block_till_done()

        # Finish download
        result = await hass.config_entries.subentries.async_configure(
            reconfigure_flow["flow_id"], {}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert subentry.data == {
        ollama.CONF_MODEL: "llama3.2:latest",
        ollama.CONF_PROMPT: "updated prompt",
        ollama.CONF_MAX_HISTORY: 75.0,
        ollama.CONF_NUM_CTX: 8192.0,
        ollama.CONF_THINK: True,
    }
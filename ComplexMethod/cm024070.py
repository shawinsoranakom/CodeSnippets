async def test_subentry_need_download(
    hass: HomeAssistant,
    mock_init_component,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test subentry creation when model needs to be downloaded."""

    async def delayed_pull(self, model: str) -> None:
        """Simulate a delayed model download."""
        assert model == "llama3.2:latest"
        await asyncio.sleep(0)  # yield the event loop 1 iteration

    with (
        patch(
            "ollama.AsyncClient.list",
            return_value={"models": [{"model": TEST_MODEL}]},
        ),
        patch("ollama.AsyncClient.pull", delayed_pull),
    ):
        new_flow = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": SOURCE_USER},
        )

        assert new_flow["type"] is FlowResultType.FORM, new_flow
        assert new_flow["step_id"] == "set_options"

        # Configure the new subentry with a model that needs downloading
        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",  # not cached
                CONF_NAME: "New Test Conversation",
                ollama.CONF_PROMPT: "new test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )

        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "download"
        assert result["progress_action"] == "download"

        await hass.async_block_till_done()

        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"], {}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "New Test Conversation"
    assert result["data"] == {
        ollama.CONF_MODEL: "llama3.2:latest",
        ollama.CONF_PROMPT: "new test prompt",
        ollama.CONF_MAX_HISTORY: 50.0,
        ollama.CONF_NUM_CTX: 16384.0,
        ollama.CONF_THINK: False,
    }
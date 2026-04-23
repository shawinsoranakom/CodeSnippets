async def test_subentry_download_error(
    hass: HomeAssistant,
    mock_init_component,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test subentry creation when model download fails."""

    async def delayed_pull(self, model: str) -> None:
        """Simulate a delayed model download."""
        await asyncio.sleep(0)  # yield

        raise RuntimeError("Download failed")

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

        assert new_flow["type"] is FlowResultType.FORM
        assert new_flow["step_id"] == "set_options"

        # Configure with a model that needs downloading but will fail
        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"],
            {
                ollama.CONF_MODEL: "llama3.2:latest",
                CONF_NAME: "New Test Conversation",
                ollama.CONF_PROMPT: "new test prompt",
                ollama.CONF_MAX_HISTORY: 50,
                ollama.CONF_NUM_CTX: 16384,
                ollama.CONF_THINK: False,
            },
        )

        # Should show progress flow result for download
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["step_id"] == "download"
        assert result["progress_action"] == "download"

        # Wait for download task to complete (with error)
        await hass.async_block_till_done()

        # Submit the progress flow - should get failure
        result = await hass.config_entries.subentries.async_configure(
            new_flow["flow_id"], {}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "download_failed"
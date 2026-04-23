async def test_creating_ai_task_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test creating an AI task subentry."""
    old_subentries = set(mock_config_entry.subentries)
    # Original conversation + original ai_task
    assert len(mock_config_entry.subentries) == 2

    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": "test_model:latest"}]},
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "ai_task_data"),
            context={"source": SOURCE_USER},
        )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "set_options"
    assert not result.get("errors")

    with patch(
        "ollama.AsyncClient.list",
        return_value={"models": [{"model": "test_model:latest"}]},
    ):
        result2 = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            {
                "name": "Custom AI Task",
                ollama.CONF_MODEL: "test_model:latest",
                ollama.CONF_MAX_HISTORY: 5,
                ollama.CONF_NUM_CTX: 4096,
                ollama.CONF_KEEP_ALIVE: 30,
                ollama.CONF_THINK: False,
            },
        )
        await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "Custom AI Task"
    assert result2.get("data") == {
        ollama.CONF_MODEL: "test_model:latest",
        ollama.CONF_MAX_HISTORY: 5,
        ollama.CONF_NUM_CTX: 4096,
        ollama.CONF_KEEP_ALIVE: 30,
        ollama.CONF_THINK: False,
    }

    assert (
        len(mock_config_entry.subentries) == 3
    )  # Original conversation + original ai_task + new ai_task

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]
    assert new_subentry.subentry_type == "ai_task_data"
    assert new_subentry.title == "Custom AI Task"
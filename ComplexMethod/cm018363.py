async def test_creating_ai_task_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_init_component,
) -> None:
    """Test creating an AI task subentry."""
    old_subentries = set(mock_config_entry.subentries)
    # Original conversation + ai_task + stt + tts
    assert len(mock_config_entry.subentries) == 4

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": config_entries.SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "init"
    assert not result.get("errors")

    result2 = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Custom AI Task",
            CONF_RECOMMENDED: True,
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2.get("title") == "Custom AI Task"
    assert result2.get("data") == {
        CONF_RECOMMENDED: True,
    }

    assert (
        len(mock_config_entry.subentries) == 5
    )  # Original conversation + stt + tts + ai_task + new ai_task

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]
    assert new_subentry.subentry_type == "ai_task_data"
    assert new_subentry.title == "Custom AI Task"
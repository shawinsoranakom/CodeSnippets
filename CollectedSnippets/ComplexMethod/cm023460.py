async def test_creating_subentry(
    hass: HomeAssistant,
    mock_init_component: None,
    mock_config_entry: MockConfigEntry,
    subentry_type: str,
    options: dict[str, Any],
) -> None:
    """Test creating a subentry."""
    old_subentries = set(mock_config_entry.subentries)

    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, subentry_type),
            context={"source": config_entries.SOURCE_USER},
        )

    assert result["type"] is FlowResultType.FORM, result
    assert result["step_id"] == "set_options"
    assert not result["errors"]

    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        result2 = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            result["data_schema"]({CONF_NAME: "Mock name", **options}),
        )
        await hass.async_block_till_done()

    expected_options = options.copy()
    if CONF_PROMPT in expected_options:
        expected_options[CONF_PROMPT] = expected_options[CONF_PROMPT].strip()
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Mock name"
    assert result2["data"] == expected_options

    assert len(mock_config_entry.subentries) == len(old_subentries) + 1

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]

    assert new_subentry.subentry_type == subentry_type
    assert new_subentry.data == expected_options
    assert new_subentry.title == "Mock name"
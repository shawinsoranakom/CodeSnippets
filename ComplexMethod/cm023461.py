async def test_creating_subentry_custom_options(
    hass: HomeAssistant,
    mock_init_component: None,
    mock_config_entry: MockConfigEntry,
    subentry_type: str,
    recommended_model: str,
    options: dict[str, Any],
) -> None:
    """Test creating a subentry with custom options."""
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

    # Uncheck recommended to show custom options
    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        result2 = await hass.config_entries.subentries.async_configure(
            result["flow_id"],
            result["data_schema"]({CONF_RECOMMENDED: False}),
        )
    assert result2["type"] is FlowResultType.FORM

    # Find the schema key for CONF_CHAT_MODEL and check its default
    schema_dict = result2["data_schema"].schema
    chat_model_key = next(key for key in schema_dict if key.schema == CONF_CHAT_MODEL)
    assert chat_model_key.default() == recommended_model
    models_in_selector = [
        opt["value"] for opt in schema_dict[chat_model_key].config["options"]
    ]
    assert recommended_model in models_in_selector

    # Submit the form
    with patch(
        "google.genai.models.AsyncModels.list",
        return_value=get_models_pager(),
    ):
        result3 = await hass.config_entries.subentries.async_configure(
            result2["flow_id"],
            result2["data_schema"]({CONF_NAME: "Mock name", **options}),
        )
        await hass.async_block_till_done()

    expected_options = options.copy()
    if CONF_PROMPT in expected_options:
        expected_options[CONF_PROMPT] = expected_options[CONF_PROMPT].strip()
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "Mock name"
    assert result3["data"] == expected_options

    assert len(mock_config_entry.subentries) == len(old_subentries) + 1

    new_subentry_id = list(set(mock_config_entry.subentries) - old_subentries)[0]
    new_subentry = mock_config_entry.subentries[new_subentry_id]

    assert new_subentry.subentry_type == subentry_type
    assert new_subentry.data == expected_options
    assert new_subentry.title == "Mock name"
async def test_repair_flow_iterates_subentries(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Test the repair flow iterates across deprecated subentries."""
    entry_one: MockConfigEntry = _make_entry(
        hass,
        title="Entry One",
        api_key="key-one",
        subentries_data=[
            {
                "data": {CONF_CHAT_MODEL: "claude-3-5-haiku-20241022"},
                "subentry_type": "conversation",
                "title": "Conversation One",
                "unique_id": None,
            },
            {
                "data": {CONF_CHAT_MODEL: "claude-3-7-sonnet-20250219"},
                "subentry_type": "ai_task_data",
                "title": "AI task One",
                "unique_id": None,
            },
        ],
    )
    entry_two: MockConfigEntry = _make_entry(
        hass,
        title="Entry Two",
        api_key="key-two",
        subentries_data=[
            {
                "data": {CONF_CHAT_MODEL: "claude-3-opus-20240229"},
                "subentry_type": "conversation",
                "title": "Conversation Two",
                "unique_id": None,
            },
        ],
    )

    ir.async_create_issue(
        hass,
        DOMAIN,
        "model_deprecated",
        is_fixable=True,
        is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key="model_deprecated",
    )

    await _setup_repairs(hass)
    client = await hass_client()

    result = await start_repair_fix_flow(client, DOMAIN, "model_deprecated")
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"
    placeholders = result["description_placeholders"]
    assert placeholders["entry_name"] == entry_one.title
    assert placeholders["subentry_name"] == "Conversation One"
    assert placeholders["subentry_type"] == "Conversation agent"
    assert placeholders["retirement_date"] == "February 19th, 2026"

    flow_id = result["flow_id"]

    result = await process_repair_fix_flow(
        client,
        flow_id,
        json={CONF_CHAT_MODEL: "claude-haiku-4-5"},
    )
    assert result["type"] == FlowResultType.FORM
    assert (
        _get_subentry(entry_one, "conversation").data[CONF_CHAT_MODEL]
        == "claude-haiku-4-5"
    )

    placeholders = result["description_placeholders"]
    assert placeholders["entry_name"] == entry_one.title
    assert placeholders["subentry_name"] == "AI task One"
    assert placeholders["subentry_type"] == "AI task"
    assert placeholders["retirement_date"] == "February 19th, 2026"

    result = await process_repair_fix_flow(
        client,
        flow_id,
        json={CONF_CHAT_MODEL: "claude-sonnet-4-6"},
    )
    assert result["type"] == FlowResultType.FORM
    assert (
        _get_subentry(entry_one, "ai_task_data").data[CONF_CHAT_MODEL]
        == "claude-sonnet-4-6"
    )
    assert (
        _get_subentry(entry_one, "conversation").data[CONF_CHAT_MODEL]
        == "claude-haiku-4-5"
    )

    placeholders = result["description_placeholders"]
    assert placeholders["entry_name"] == entry_two.title
    assert placeholders["subentry_name"] == "Conversation Two"
    assert placeholders["subentry_type"] == "Conversation agent"
    assert placeholders["retirement_date"] == "January 5th, 2026"

    result = await process_repair_fix_flow(
        client,
        flow_id,
        json={CONF_CHAT_MODEL: "claude-opus-4-6"},
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert (
        _get_subentry(entry_two, "conversation").data[CONF_CHAT_MODEL]
        == "claude-opus-4-6"
    )

    assert issue_registry.async_get_issue(DOMAIN, "model_deprecated") is None
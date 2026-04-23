async def _check_config_flow_result_translations(
    manager: FlowManager,
    flow: FlowHandler,
    result: FlowResult[FlowContext, str],
    translation_errors: dict[str, str],
    ignore_translations_for_mock_domains: set[str],
) -> None:
    if result["type"] is FlowResultType.CREATE_ENTRY:
        # No need to check translations for a completed flow
        return

    key_prefix = ""
    description_placeholders = result.get("description_placeholders")
    if isinstance(manager, ConfigEntriesFlowManager):
        category = "config"
        integration = flow.handler
    elif isinstance(manager, OptionsFlowManager):
        category = "options"
        integration = flow.hass.config_entries.async_get_entry(flow.handler).domain
    elif isinstance(manager, repairs.RepairsFlowManager):
        category = "issues"
        integration = flow.handler
        issue_id = flow.issue_id
        issue = ir.async_get(flow.hass).async_get_issue(integration, issue_id)
        if issue is None:
            # Issue was deleted mid-flow (e.g., config entry removed), skip check
            return
        key_prefix = f"{issue.translation_key}.fix_flow."
        description_placeholders = {
            # Both are used in issue translations, and description_placeholders
            # takes precedence over translation_placeholders
            **(issue.translation_placeholders or {}),
            **(description_placeholders or {}),
        }
    else:
        return

    # Check if this flow has been seen before
    # Gets set to False on first run, and to True on subsequent runs
    setattr(flow, "__flow_seen_before", hasattr(flow, "__flow_seen_before"))

    if result["type"] is FlowResultType.FORM:
        if step_id := result.get("step_id"):
            await _check_step_or_section_translations(
                flow.hass,
                translation_errors,
                category,
                integration,
                f"{key_prefix}step.{step_id}",
                description_placeholders,
                result["data_schema"],
                ignore_translations_for_mock_domains,
            )

        if errors := result.get("errors"):
            for error in errors.values():
                await _validate_translation(
                    flow.hass,
                    translation_errors,
                    ignore_translations_for_mock_domains,
                    category,
                    integration,
                    f"{key_prefix}error.{error}",
                    description_placeholders,
                )
        return

    if result["type"] is FlowResultType.ABORT:
        # We don't need translations for a discovery flow which immediately
        # aborts, since such flows won't be seen by users
        if not flow.__flow_seen_before and flow.source in DISCOVERY_SOURCES:
            return
        await _validate_translation(
            flow.hass,
            translation_errors,
            ignore_translations_for_mock_domains,
            category,
            integration,
            f"{key_prefix}abort.{result['reason']}",
            description_placeholders,
        )
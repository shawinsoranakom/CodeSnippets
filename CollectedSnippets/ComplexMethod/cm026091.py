async def async_generate_data(
    hass: HomeAssistant,
    *,
    task_name: str,
    entity_id: str | None = None,
    instructions: str,
    structure: vol.Schema | None = None,
    attachments: list[dict] | None = None,
    llm_api: llm.API | None = None,
) -> GenDataTaskResult:
    """Run a data generation task in the AI Task integration."""
    if entity_id is None:
        entity_id = hass.data[DATA_PREFERENCES].gen_data_entity_id

    if entity_id is None:
        raise HomeAssistantError("No entity_id provided and no preferred entity set")

    entity = hass.data[DATA_COMPONENT].get_entity(entity_id)
    if entity is None:
        raise HomeAssistantError(f"AI Task entity {entity_id} not found")

    if AITaskEntityFeature.GENERATE_DATA not in entity.supported_features:
        raise HomeAssistantError(
            f"AI Task entity {entity_id} does not support generating data"
        )

    if (
        attachments
        and AITaskEntityFeature.SUPPORT_ATTACHMENTS not in entity.supported_features
    ):
        raise HomeAssistantError(
            f"AI Task entity {entity_id} does not support attachments"
        )

    with async_get_chat_session(hass) as session:
        resolved_attachments = await _resolve_attachments(hass, session, attachments)

        return await entity.internal_async_generate_data(
            session,
            GenDataTask(
                name=task_name,
                instructions=instructions,
                structure=structure,
                attachments=resolved_attachments or None,
                llm_api=llm_api,
            ),
        )
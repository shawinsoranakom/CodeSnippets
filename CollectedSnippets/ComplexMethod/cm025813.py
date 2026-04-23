async def _get_tasks(call: ServiceCall) -> ServiceResponse:
    """Get tasks action."""

    entry: HabiticaConfigEntry = service.async_get_config_entry(
        call.hass, DOMAIN, call.data[ATTR_CONFIG_ENTRY]
    )
    coordinator = entry.runtime_data
    response: list[TaskData] = coordinator.data.tasks

    if types := {TaskType[x] for x in call.data.get(ATTR_TYPE, [])}:
        response = [task for task in response if task.Type in types]

    if priority := {TaskPriority[x] for x in call.data.get(ATTR_PRIORITY, [])}:
        response = [task for task in response if task.priority in priority]

    if tasks := call.data.get(ATTR_TASK):
        response = [
            task
            for task in response
            if str(task.id) in tasks or task.alias in tasks or task.text in tasks
        ]

    if tags := call.data.get(ATTR_TAG):
        tag_ids = {
            tag.id
            for tag in coordinator.data.user.tags
            if (tag.name and tag.name.lower())
            in (tag.lower() for tag in tags)  # Case-insensitive matching
            and tag.id
        }

        response = [
            task
            for task in response
            if any(tag_id in task.tags for tag_id in tag_ids if task.tags)
        ]
    if keyword := call.data.get(ATTR_KEYWORD):
        keyword = keyword.lower()
        response = [
            task
            for task in response
            if (task.text and keyword in task.text.lower())
            or (task.notes and keyword in task.notes.lower())
            or any(keyword in item.text.lower() for item in task.checklist)
        ]
    result: dict[str, Any] = {
        "tasks": [task.to_dict(omit_none=False) for task in response]
    }

    return result
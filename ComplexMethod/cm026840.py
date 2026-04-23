def _todo_item(resource: caldav.CalendarObjectResource) -> TodoItem | None:
    """Convert a caldav Todo into a TodoItem."""
    if (
        not hasattr(resource.instance, "vtodo")
        or not (todo := resource.instance.vtodo)
        or (uid := get_attr_value(todo, "uid")) is None
        or (summary := get_attr_value(todo, "summary")) is None
    ):
        return None
    due: date | datetime | None = None
    if due_value := get_attr_value(todo, "due"):
        if isinstance(due_value, datetime):
            due = dt_util.as_local(due_value)
        elif isinstance(due_value, date):
            due = due_value
    return TodoItem(
        uid=uid,
        summary=summary,
        status=TODO_STATUS_MAP.get(
            get_attr_value(todo, "status") or "",
            TodoItemStatus.NEEDS_ACTION,
        ),
        due=due,
        description=get_attr_value(todo, "description"),
    )
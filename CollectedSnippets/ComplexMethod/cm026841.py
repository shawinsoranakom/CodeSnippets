async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        uid: str = cast(str, item.uid)
        try:
            todo = await self.hass.async_add_executor_job(
                self._calendar.todo_by_uid, uid
            )
        except NotFoundError as err:
            raise HomeAssistantError(f"Could not find To-do item {uid}") from err
        except (requests.ConnectionError, DAVError) as err:
            raise HomeAssistantError(f"CalDAV lookup error: {err}") from err
        vtodo = todo.icalendar_component  # type: ignore[attr-defined]
        vtodo["SUMMARY"] = item.summary or ""
        if status := item.status:
            vtodo["STATUS"] = TODO_STATUS_MAP_INV.get(status, "NEEDS-ACTION")
        if due := item.due:
            todo.set_due(due)  # type: ignore[attr-defined]
        else:
            vtodo.pop("DUE", None)
        if description := item.description:
            vtodo["DESCRIPTION"] = description
        else:
            vtodo.pop("DESCRIPTION", None)
        try:
            await self.hass.async_add_executor_job(
                partial(
                    todo.save,
                    no_create=True,
                    obj_type="todo",
                ),
            )
            # refreshing async otherwise it would take too much time
            self.hass.async_create_task(self.async_update_ha_state(force_refresh=True))
        except (requests.ConnectionError, DAVError) as err:
            raise HomeAssistantError(f"CalDAV save error: {err}") from err
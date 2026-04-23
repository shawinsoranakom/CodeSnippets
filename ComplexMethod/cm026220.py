async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update a To-do item."""
        uid: str = cast(str, item.uid)
        api_data = next((d for d in self.coordinator.data if d.id == uid), None)
        if update_data := _task_api_data(item, api_data):
            await self.coordinator.api.update_task(task_id=uid, **update_data)
        if item.status is not None:
            # Only update status if changed
            for existing_item in self._attr_todo_items or ():
                if existing_item.uid != item.uid:
                    continue

                if item.status != existing_item.status:
                    if item.status == TodoItemStatus.COMPLETED:
                        await self.coordinator.api.complete_task(task_id=uid)
                    else:
                        await self.coordinator.api.uncomplete_task(task_id=uid)
        await self.coordinator.async_refresh()
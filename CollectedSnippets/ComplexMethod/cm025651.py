async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Re-order an item to the To-do list."""
        if uid == previous_uid:
            return
        async with self._calendar_lock:
            todos = self._calendar.todos
            item_idx: dict[str, int] = {itm.uid: idx for idx, itm in enumerate(todos)}
            if uid not in item_idx:
                raise HomeAssistantError(
                    f"Item '{uid}' not found in todo list {self.entity_id}"
                )
            if previous_uid and previous_uid not in item_idx:
                raise HomeAssistantError(
                    f"Item '{previous_uid}' not found in todo list {self.entity_id}"
                )
            dst_idx = item_idx[previous_uid] + 1 if previous_uid else 0
            src_idx = item_idx[uid]
            src_item = todos.pop(src_idx)
            if dst_idx > src_idx:
                dst_idx -= 1
            todos.insert(dst_idx, src_item)
            await self.async_save()
        await self.async_update_ha_state(force_refresh=True)
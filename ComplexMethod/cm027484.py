async def _async_do_handle(self, target_list: TodoListEntity, item: str) -> None:
        """Execute action specific to this intent handler."""

        # Find item in list
        matching_item = None
        for todo_item in target_list.todo_items or ():
            if (
                item == todo_item.uid
                or item.casefold() == (todo_item.summary or "").casefold()
            ):
                matching_item = todo_item
                break
        if not matching_item or not matching_item.uid:
            raise intent.IntentHandleError(
                f"Item '{item}' not found on list", "item_not_found"
            )

        # Remove items
        await target_list.async_delete_todo_items(uids=[matching_item.uid])
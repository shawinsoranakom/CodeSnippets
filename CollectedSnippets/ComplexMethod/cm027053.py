async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item to the To-do list.

        Bring has an internal 'recent' list which we want to use instead of a todo list
        status, therefore completed todo list items are matched to the recent list and
        pending items to the purchase list.

        This results in following behaviour:

        - Completed items will move to the "completed" section in home assistant todo
            list and get moved to the recently list in bring
        - Bring shows some odd behaviour when renaming items. This is because Bring
            did not have unique identifiers for items in the past and this is still
            a relic from it. Therefore the name is not to be changed! Should a name
            be changed anyway, the item will be deleted and a new item will be created
            instead and no update for this item is performed and on the next cloud pull
            update, it will get cleared and replaced seamlessly.
        """

        bring_list = self.bring_list

        current_item = next(
            (
                i
                for i in chain(
                    bring_list.content.items.purchase, bring_list.content.items.recently
                )
                if i.uuid == item.uid
            ),
            None,
        )

        if TYPE_CHECKING:
            assert item.uid
            assert current_item

        if item.summary == current_item.itemId:
            try:
                await self.coordinator.bring.batch_update_list(
                    self._list_uuid,
                    BringItem(
                        itemId=item.summary or "",
                        spec=item.description or "",
                        uuid=item.uid,
                    ),
                    BringItemOperation.ADD
                    if item.status == TodoItemStatus.NEEDS_ACTION
                    else BringItemOperation.COMPLETE,
                )
            except BringRequestException as e:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="todo_update_item_failed",
                    translation_placeholders={"name": item.summary or ""},
                ) from e
        else:
            try:
                await self.coordinator.bring.batch_update_list(
                    self._list_uuid,
                    [
                        BringItem(
                            itemId=current_item.itemId,
                            spec=item.description or "",
                            uuid=item.uid,
                            operation=BringItemOperation.REMOVE,
                        ),
                        BringItem(
                            itemId=item.summary or "",
                            spec=item.description or "",
                            uuid=str(uuid.uuid4()),
                            operation=BringItemOperation.ADD
                            if item.status == TodoItemStatus.NEEDS_ACTION
                            else BringItemOperation.COMPLETE,
                        ),
                    ],
                )

            except BringRequestException as e:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="todo_rename_item_failed",
                    translation_placeholders={"name": item.summary or ""},
                ) from e

        await self.coordinator.async_refresh()
async def async_update_todo_item(self, item: TodoItem) -> None:
        """Update an item on the list."""
        list_items = self.shopping_items

        list_item: ShoppingItem | None = next(
            (x for x in list_items if x.item_id == item.uid), None
        )
        assert list_item is not None
        position = list_item.position

        update_shopping_item = MutateShoppingItem(
            item_id=list_item.item_id,
            list_id=list_item.list_id,
            note=list_item.note,
            display=list_item.display,
            checked=item.status == TodoItemStatus.COMPLETED,
            position=position,
            is_food=list_item.is_food,
            disable_amount=list_item.disable_amount,
            quantity=list_item.quantity,
            label_id=list_item.label_id,
            food_id=list_item.food_id,
            unit_id=list_item.unit_id,
        )

        stripped_item_summary = item.summary.strip() if item.summary else item.summary

        if list_item.display.strip() != stripped_item_summary:
            update_shopping_item.note = stripped_item_summary
            update_shopping_item.position = position
            if update_shopping_item.is_food is not None:
                update_shopping_item.is_food = False
            update_shopping_item.food_id = None
            update_shopping_item.quantity = 0.0
            update_shopping_item.checked = item.status == TodoItemStatus.COMPLETED

        try:
            await self.coordinator.client.update_shopping_item(
                list_item.item_id, update_shopping_item
            )
        except MealieError as exception:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="update_item_error",
                translation_placeholders={
                    "shopping_list_name": self.shopping_list.name
                },
            ) from exception
        finally:
            await self.coordinator.async_refresh()
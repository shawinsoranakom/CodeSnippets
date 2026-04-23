async def async_move_todo_item(
        self, uid: str, previous_uid: str | None = None
    ) -> None:
        """Re-order an item on the list."""
        if uid == previous_uid:
            return
        list_items: list[ShoppingItem] = self.shopping_items

        item_idx = {itm.item_id: idx for idx, itm in enumerate(list_items)}
        if uid not in item_idx:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="item_not_found_error",
                translation_placeholders={"shopping_list_item": uid},
            )
        if previous_uid and previous_uid not in item_idx:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="item_not_found_error",
                translation_placeholders={"shopping_list_item": previous_uid},
            )
        dst_idx = item_idx[previous_uid] + 1 if previous_uid else 0
        src_idx = item_idx[uid]
        src_item = list_items.pop(src_idx)
        if dst_idx > src_idx:
            dst_idx -= 1
        list_items.insert(dst_idx, src_item)

        for position, item in enumerate(list_items):
            mutate_shopping_item = MutateShoppingItem()
            mutate_shopping_item.list_id = item.list_id
            mutate_shopping_item.item_id = item.item_id
            mutate_shopping_item.position = position
            mutate_shopping_item.is_food = item.is_food
            mutate_shopping_item.quantity = item.quantity
            mutate_shopping_item.label_id = item.label_id
            mutate_shopping_item.note = item.note
            mutate_shopping_item.checked = item.checked

            if item.is_food or item.food_id:
                mutate_shopping_item.food_id = item.food_id
                mutate_shopping_item.unit_id = item.unit_id

            await self.coordinator.client.update_shopping_item(
                mutate_shopping_item.item_id, mutate_shopping_item
            )

        await self.coordinator.async_refresh()
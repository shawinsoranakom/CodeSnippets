async def async_move_item(self, uid: str, previous: str | None = None) -> None:
        """Re-order a shopping list item."""
        if uid == previous:
            return
        item_idx = {cast(str, itm["id"]): idx for idx, itm in enumerate(self.items)}
        if uid not in item_idx:
            raise NoMatchingShoppingListItem(f"Item '{uid}' not found in shopping list")
        if previous and previous not in item_idx:
            raise NoMatchingShoppingListItem(
                f"Item '{previous}' not found in shopping list"
            )
        dst_idx = item_idx[previous] + 1 if previous else 0
        src_idx = item_idx[uid]
        src_item = self.items.pop(src_idx)
        if dst_idx > src_idx:
            dst_idx -= 1
        self.items.insert(dst_idx, src_item)
        await self.hass.async_add_executor_job(self.save)
        self._async_notify()
        self.hass.bus.async_fire(
            EVENT_SHOPPING_LIST_UPDATED,
            {"action": "reorder"},
        )
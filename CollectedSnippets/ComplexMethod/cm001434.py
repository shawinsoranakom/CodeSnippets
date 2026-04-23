def _parse_todo_item(
        self, item: dict, path: str = "Item"
    ) -> tuple[Optional[TodoItem], Optional[str]]:
        """
        Recursively parse a dict into a TodoItem with sub_items.

        Returns (TodoItem, None) on success or (None, error_message) on failure.
        """
        # Check required fields
        if not item.get("content"):
            return None, f"{path}: 'content' is required and must be non-empty"
        if not item.get("active_form"):
            return None, f"{path}: 'active_form' is required and must be non-empty"
        if item.get("status") not in ("pending", "in_progress", "completed"):
            return (
                None,
                f"{path}: 'status' must be one of: pending, in_progress, completed",
            )

        # Parse sub_items recursively
        sub_items = []
        raw_sub_items = item.get("sub_items", [])
        if raw_sub_items:
            for j, sub_item in enumerate(raw_sub_items):
                parsed, error = self._parse_todo_item(
                    sub_item, f"{path}.sub_items[{j}]"
                )
                if error:
                    return None, error
                if parsed:
                    sub_items.append(parsed)

        # Use provided ID or generate a new one
        item_id = item.get("id") or _generate_todo_id()

        return (
            TodoItem(
                id=item_id,
                content=item["content"],
                status=item["status"],
                active_form=item["active_form"],
                sub_items=sub_items,
            ),
            None,
        )
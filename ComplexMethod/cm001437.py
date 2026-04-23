def todo_add(
        self,
        content: str,
        active_form: str,
        status: TodoStatus = "pending",
        index: Optional[int] = None,
    ) -> dict:
        """
        Add a single todo item. Returns the created item with its ID.

        This is the most token-efficient way to add a new task.
        Use this instead of todo_write when adding one item to an existing list.
        """
        # Validate inputs
        if not content or not content.strip():
            return {"status": "error", "message": "'content' is required"}
        if not active_form or not active_form.strip():
            return {"status": "error", "message": "'active_form' is required"}

        # Check max items
        if len(self._todos.items) >= self.config.max_items:
            return {
                "status": "error",
                "message": f"Cannot add: max items ({self.config.max_items}) reached",
            }

        # Create the new item
        new_item = TodoItem(
            content=content.strip(),
            active_form=active_form.strip(),
            status=status,
        )

        # Insert at specified index or append
        if index is not None:
            if index < 0:
                index = 0
            if index > len(self._todos.items):
                index = len(self._todos.items)
            self._todos.items.insert(index, new_item)
        else:
            self._todos.items.append(new_item)

        return {
            "status": "success",
            "item": self._serialize_todo_item(new_item),
            "total_items": len(self._todos.items),
        }
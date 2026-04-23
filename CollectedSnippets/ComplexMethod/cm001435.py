def todo_read(self) -> dict:
        """
        Get the current todo list.

        Returns all todos with their current statuses and sub-items.
        Useful for reviewing progress or understanding current state.
        """
        return {
            "status": "success",
            "items": [self._serialize_todo_item(t) for t in self._todos.items],
            "summary": {
                "pending": sum(1 for t in self._todos.items if t.status == "pending"),
                "in_progress": sum(
                    1 for t in self._todos.items if t.status == "in_progress"
                ),
                "completed": sum(
                    1 for t in self._todos.items if t.status == "completed"
                ),
            },
        }
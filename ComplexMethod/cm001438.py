def todo_update(
        self,
        id: str,
        content: Optional[str] = None,
        active_form: Optional[str] = None,
        status: Optional[TodoStatus] = None,
    ) -> dict:
        """
        Partial update of a todo - only specified fields change.

        Use this when you need to update multiple fields at once.
        For just status changes, prefer todo_set_status.
        """
        item = self._find_by_id(id)
        if not item:
            return {"status": "error", "message": f"Todo with ID '{id}' not found"}

        changes: dict[str, dict[str, str]] = {}

        if content is not None:
            if not content.strip():
                return {"status": "error", "message": "'content' cannot be empty"}
            changes["content"] = {"from": item.content, "to": content.strip()}
            item.content = content.strip()

        if active_form is not None:
            if not active_form.strip():
                return {"status": "error", "message": "'active_form' cannot be empty"}
            changes["active_form"] = {
                "from": item.active_form,
                "to": active_form.strip(),
            }
            item.active_form = active_form.strip()

        if status is not None:
            changes["status"] = {"from": item.status, "to": status}
            item.status = status

        if not changes:
            return {
                "status": "success",
                "item": self._serialize_todo_item(item),
                "message": "No changes specified",
            }

        return {
            "status": "success",
            "item": self._serialize_todo_item(item),
            "changed": changes,
        }
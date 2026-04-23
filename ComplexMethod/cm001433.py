def get_messages(self) -> Iterator[ChatMessage]:
        if not self.config.show_in_prompt or not self._todos.items:
            return

        in_progress = [t for t in self._todos.items if t.status == "in_progress"]
        pending = [t for t in self._todos.items if t.status == "pending"]
        completed = [t for t in self._todos.items if t.status == "completed"]

        lines = ["## Your Todo List\n"]

        # Show in-progress first (most important) with sub-items
        if in_progress:
            lines.append("**Currently working on:**")
            for todo in in_progress:
                lines.extend(self._format_todo_item(todo))

        # Show pending with sub-items
        if pending:
            lines.append("\n**Pending:**")
            for todo in pending:
                lines.extend(self._format_todo_item(todo))

        # Show completed (brief summary)
        if completed:
            lines.append(f"\n**Completed:** {len(completed)} task(s)")

        yield ChatMessage.user("\n".join(lines))
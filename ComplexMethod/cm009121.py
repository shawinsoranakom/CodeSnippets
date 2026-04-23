def _moderate_inputs(
        self, messages: Sequence[BaseMessage]
    ) -> dict[str, Any] | None:
        working = list(messages)
        modified = False

        if self.check_tool_results:
            action = self._moderate_tool_messages(working)
            if action:
                if "jump_to" in action:
                    return action
                working = cast("list[BaseMessage]", action["messages"])
                modified = True

        if self.check_input:
            action = self._moderate_user_message(working)
            if action:
                if "jump_to" in action:
                    return action
                working = cast("list[BaseMessage]", action["messages"])
                modified = True

        if modified:
            return {"messages": working}

        return None
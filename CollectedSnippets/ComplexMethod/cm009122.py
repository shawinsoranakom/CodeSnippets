async def _amoderate_inputs(
        self, messages: Sequence[BaseMessage]
    ) -> dict[str, Any] | None:
        working = list(messages)
        modified = False

        if self.check_tool_results:
            action = await self._amoderate_tool_messages(working)
            if action:
                if "jump_to" in action:
                    return action
                working = cast("list[BaseMessage]", action["messages"])
                modified = True

        if self.check_input:
            action = await self._amoderate_user_message(working)
            if action:
                if "jump_to" in action:
                    return action
                working = cast("list[BaseMessage]", action["messages"])
                modified = True

        if modified:
            return {"messages": working}

        return None
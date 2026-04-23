async def _amoderate_tool_messages(
        self, messages: Sequence[BaseMessage]
    ) -> dict[str, Any] | None:
        last_ai_idx = self._find_last_index(messages, AIMessage)
        if last_ai_idx is None:
            return None

        working = list(messages)
        modified = False

        for idx in range(last_ai_idx + 1, len(working)):
            msg = working[idx]
            if not isinstance(msg, ToolMessage):
                continue

            text = self._extract_text(msg)
            if not text:
                continue

            result = await self._amoderate(text)
            if not result.flagged:
                continue

            action = self._apply_violation(
                working, index=idx, stage="tool", content=text, result=result
            )
            if action:
                if "jump_to" in action:
                    return action
                working = cast("list[BaseMessage]", action["messages"])
                modified = True

        if modified:
            return {"messages": working}

        return None
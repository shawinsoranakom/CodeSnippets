def has_tool_been_called(self, tool_name: str) -> bool:
        """True when *tool_name* has been called in this session.

        Checks the in-flight announcement buffer (for calls dispatched
        in the *current* turn but not yet flushed into ``messages``) and
        the durable ``messages`` history (for past turns + prior rounds
        within this turn whose writes already landed).  The durable
        scan is session-wide, not turn-scoped: a matching tool call
        anywhere in ``messages`` counts.  This matches the guide-read
        contract — once the guide has been read in the session, the
        agent doesn't need to re-read it for later create/edit/fix
        tools.
        """
        if tool_name in self._inflight_tool_calls:
            return True
        for msg in reversed(self.messages):
            if msg.role != "assistant" or not msg.tool_calls:
                continue
            for tc in msg.tool_calls:
                name = tc.get("function", {}).get("name") or tc.get("name")
                if name == tool_name:
                    return True
        return False
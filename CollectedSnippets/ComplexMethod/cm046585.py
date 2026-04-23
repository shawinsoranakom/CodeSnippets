def _validate_role_shape(self) -> "ChatMessage":
        # Enforce the per-role OpenAI spec shape at the request boundary.
        # Without this, malformed messages (e.g. user entries with no
        # content, tool_calls on a user/system role, role="tool" without
        # tool_call_id) would be silently forwarded to llama-server via
        # the passthrough path, surfacing as opaque upstream errors or
        # broken tool-call reconciliation downstream.

        # Tool-call metadata must appear only on the appropriate role.
        if self.tool_calls is not None and self.role != "assistant":
            raise ValueError('"tool_calls" is only valid on role="assistant" messages.')
        if self.tool_call_id is not None and self.role != "tool":
            raise ValueError('"tool_call_id" is only valid on role="tool" messages.')
        if self.name is not None and self.role != "tool":
            raise ValueError('"name" is only valid on role="tool" messages.')

        # Per-role content requirements.
        if self.role == "tool":
            if not self.tool_call_id:
                raise ValueError(
                    'role="tool" messages require "tool_call_id" per the OpenAI spec.'
                )
            if not self.content:
                raise ValueError('role="tool" messages require non-empty "content".')
        elif self.role == "assistant":
            # Assistant messages may omit content when tool_calls is set.
            if not self.content and not self.tool_calls:
                raise ValueError(
                    'role="assistant" messages require either "content" or "tool_calls".'
                )
        else:  # "user" | "system"
            if not self.content:
                raise ValueError(
                    f'role="{self.role}" messages require non-empty "content".'
                )
        return self
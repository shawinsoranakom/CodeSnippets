def test_instructions_plus_developer_message_are_merged(self):
        """Codex CLI sends `instructions` (system prompt) AND a developer
        message in `input`. Strict chat templates (harmony / gpt-oss, Qwen3,
        ...) raise "System message must be at the beginning" when two
        separate system-role messages appear, so we must emit exactly one
        merged system message at the top.
        """
        payload = ResponsesRequest(
            instructions = "Base instructions.",
            input = [
                {"role": "developer", "content": "Developer override."},
                {"role": "user", "content": "Hi"},
            ],
        )
        msgs = _normalise_responses_input(payload)
        system_roles = [m for m in msgs if m.role == "system"]
        assert len(system_roles) == 1
        assert "Base instructions." in system_roles[0].content
        assert "Developer override." in system_roles[0].content
        # System must be the very first message for strict templates.
        assert msgs[0].role == "system"
        assert msgs[1].role == "user"
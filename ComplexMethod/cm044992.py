def _render_hook_invocation(self, command: Any) -> str:
        """Render an agent-specific invocation string for a hook command."""
        if not isinstance(command, str):
            return ""

        command_id = command.strip()
        if not command_id:
            return ""

        init_options = self._load_init_options()
        selected_ai = init_options.get("ai")
        codex_skill_mode = selected_ai == "codex" and bool(init_options.get("ai_skills"))
        claude_skill_mode = selected_ai == "claude" and bool(init_options.get("ai_skills"))
        kimi_skill_mode = selected_ai == "kimi"
        cursor_skill_mode = selected_ai == "cursor-agent" and bool(init_options.get("ai_skills"))

        skill_name = self._skill_name_from_command(command_id)
        if codex_skill_mode and skill_name:
            return f"${skill_name}"
        if claude_skill_mode and skill_name:
            return f"/{skill_name}"
        if kimi_skill_mode and skill_name:
            return f"/skill:{skill_name}"
        if cursor_skill_mode and skill_name:
            return f"/{skill_name}"

        return f"/{command_id}"
def format_hook_message(
        self, event_name: str, hooks: List[Dict[str, Any]]
    ) -> str:
        """Format hook execution message for display in command output.

        Args:
            event_name: Name of the event
            hooks: List of hooks to execute

        Returns:
            Formatted message string
        """
        if not hooks:
            return ""

        lines = ["\n## Extension Hooks\n"]
        lines.append(f"Hooks available for event '{event_name}':\n")

        for hook in hooks:
            extension = hook.get("extension")
            command = hook.get("command")
            invocation = self._render_hook_invocation(command)
            command_text = command if isinstance(command, str) and command.strip() else "<missing command>"
            display_invocation = invocation or (
                f"/{command_text}" if command_text != "<missing command>" else "/<missing command>"
            )
            optional = hook.get("optional", True)
            prompt = hook.get("prompt", "")
            description = hook.get("description", "")

            if optional:
                lines.append(f"\n**Optional Hook**: {extension}")
                lines.append(f"Command: `{display_invocation}`")
                if description:
                    lines.append(f"Description: {description}")
                lines.append(f"\nPrompt: {prompt}")
                lines.append(f"To execute: `{display_invocation}`")
            else:
                lines.append(f"\n**Automatic Hook**: {extension}")
                lines.append(f"Executing: `{display_invocation}`")
                lines.append(f"EXECUTE_COMMAND: {command_text}")
                lines.append(f"EXECUTE_COMMAND_INVOCATION: {display_invocation}")

        return "\n".join(lines)
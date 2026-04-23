def _format_args(self, command_name: str, arguments: dict[str, Any]) -> str:
        """Format command arguments for pattern matching.

        Args:
            command_name: Name of the command.
            arguments: Command arguments dict.

        Returns:
            Formatted arguments string.
        """
        # For file operations, use the resolved file path for symlink handling
        if command_name in (
            "read_file",
            "write_file",
            "write_to_file",
            "create_file",
            "list_folder",
        ):
            path = arguments.get("filename") or arguments.get("path") or ""
            if path:
                p = Path(path)
                if not p.is_absolute():
                    p = self.workspace / p
                return str(p.resolve())
            return ""

        # For shell commands, format as "executable:args" (first word is executable)
        if command_name in ("execute_shell", "execute_python"):
            cmd = arguments.get("command_line") or arguments.get("code") or ""
            if not cmd:
                return ""
            parts = str(cmd).split(maxsplit=1)
            if len(parts) == 2:
                return f"{parts[0]}:{parts[1]}"
            return f"{parts[0]}:"

        # For web operations
        if command_name == "web_search":
            query = arguments.get("query", "")
            return str(query)
        if command_name == "read_webpage":
            url = arguments.get("url", "")
            return str(url)

        # Generic: join all argument values
        if arguments:
            return ":".join(str(v) for v in arguments.values())
        return "*"
def _handle_view(self, args: dict, tool_call_id: str | None) -> Command:
        """Handle view command."""
        path = args["path"]
        full_path = self._validate_and_resolve_path(path)

        if not full_path.exists() or not full_path.is_file():
            msg = f"File not found: {path}"
            raise FileNotFoundError(msg)

        # Check file size
        if full_path.stat().st_size > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / 1024 / 1024
            msg = f"File too large: {path} exceeds {max_mb}MB"
            raise ValueError(msg)

        # Read file
        try:
            content = full_path.read_text()
        except UnicodeDecodeError as e:
            msg = f"Cannot decode file {path}: {e}"
            raise ValueError(msg) from e

        # Format with line numbers
        lines = content.split("\n")
        # Remove trailing newline's empty string if present
        if lines and lines[-1] == "":
            lines = lines[:-1]
        formatted_lines = [f"{i + 1}|{line}" for i, line in enumerate(lines)]
        formatted_content = "\n".join(formatted_lines)

        return Command(
            update={
                "messages": [
                    ToolMessage(
                        content=formatted_content,
                        tool_call_id=tool_call_id,
                        name=self.tool_name,
                    )
                ]
            }
        )
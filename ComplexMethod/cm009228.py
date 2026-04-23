def file_tool(
            runtime: ToolRuntime,
            command: str,
            path: str,
            file_text: str | None = None,
            old_str: str | None = None,
            new_str: str | None = None,
            insert_line: int | None = None,
            new_path: str | None = None,
            view_range: list[int] | None = None,
        ) -> Command | str:
            """Execute file operations on filesystem.

            Args:
                runtime: Tool runtime providing `tool_call_id`.
                command: Operation to perform.
                path: File path to operate on.
                file_text: Full file content for create command.
                old_str: String to replace for `str_replace` command.
                new_str: Replacement string for `str_replace` command.
                insert_line: Line number for insert command.
                new_path: New path for rename command.
                view_range: Line range `[start, end]` for view command.

            Returns:
                Command for message update or string result.
            """
            # Build args dict for handler methods
            args: dict[str, Any] = {"path": path}
            if file_text is not None:
                args["file_text"] = file_text
            if old_str is not None:
                args["old_str"] = old_str
            if new_str is not None:
                args["new_str"] = new_str
            if insert_line is not None:
                args["insert_line"] = insert_line
            if new_path is not None:
                args["new_path"] = new_path
            if view_range is not None:
                args["view_range"] = view_range

            # Route to appropriate handler based on command
            try:
                if command == "view":
                    return self._handle_view(args, runtime.tool_call_id)
                if command == "create":
                    return self._handle_create(args, runtime.tool_call_id)
                if command == "str_replace":
                    return self._handle_str_replace(args, runtime.tool_call_id)
                if command == "insert":
                    return self._handle_insert(args, runtime.tool_call_id)
                if command == "delete":
                    return self._handle_delete(args, runtime.tool_call_id)
                if command == "rename":
                    return self._handle_rename(args, runtime.tool_call_id)
                return f"Unknown command: {command}"
            except (ValueError, FileNotFoundError, PermissionError) as e:
                return str(e)
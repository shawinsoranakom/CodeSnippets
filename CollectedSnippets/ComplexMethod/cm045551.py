async def execute(
        self,
        *,
        command: Command,
        path: str,
        file_text: str | None = None,
        view_range: list[int] | None = None,
        old_str: str | None = None,
        new_str: str | None = None,
        insert_line: int | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute a file operation command."""
        # Get the appropriate file operator
        operator = self._get_operator()

        # Validate path and command combination
        await self.validate_path(command, Path(path), operator)

        # Execute the appropriate command
        if command == "view":
            result = await self.view(path, view_range, operator)
        elif command == "create":
            if file_text is None:
                raise ToolError("Parameter `file_text` is required for command: create")
            await operator.write_file(path, file_text)
            self._file_history[path].append(file_text)
            result = ToolResult(output=f"File created successfully at: {path}")
        elif command == "str_replace":
            if old_str is None:
                raise ToolError(
                    "Parameter `old_str` is required for command: str_replace"
                )
            result = await self.str_replace(path, old_str, new_str, operator)
        elif command == "insert":
            if insert_line is None:
                raise ToolError(
                    "Parameter `insert_line` is required for command: insert"
                )
            if new_str is None:
                raise ToolError("Parameter `new_str` is required for command: insert")
            result = await self.insert(path, insert_line, new_str, operator)
        elif command == "undo_edit":
            result = await self.undo_edit(path, operator)
        else:
            # This should be caught by type checking, but we include it for safety
            raise ToolError(
                f'Unrecognized command {command}. The allowed commands for the {self.name} tool are: {", ".join(get_args(Command))}'
            )

        return str(result)
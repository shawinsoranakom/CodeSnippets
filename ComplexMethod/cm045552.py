async def validate_path(
        self, command: str, path: Path, operator: FileOperator
    ) -> None:
        """Validate path and command combination based on execution environment."""
        # Check if path is absolute
        if not path.is_absolute():
            raise ToolError(f"The path {path} is not an absolute path")

        # Only check if path exists for non-create commands
        if command != "create":
            if not await operator.exists(path):
                raise ToolError(
                    f"The path {path} does not exist. Please provide a valid path."
                )

            # Check if path is a directory
            is_dir = await operator.is_directory(path)
            if is_dir and command != "view":
                raise ToolError(
                    f"The path {path} is a directory and only the `view` command can be used on directories"
                )

        # Check if file exists for create command
        elif command == "create":
            exists = await operator.exists(path)
            if exists:
                raise ToolError(
                    f"File already exists at: {path}. Cannot overwrite files using command `create`."
                )
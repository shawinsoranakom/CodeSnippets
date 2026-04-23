def validate_path(self, command: str, path: Path):
        """
        Check that the path/command combination is valid.
        """
        # Check if its an absolute path
        if not path.is_absolute():
            suggested_path = Path("") / path
            raise ToolError(
                f"The path {path} is not an absolute path, it should start with `/`. Maybe you meant {suggested_path}?"
            )
        # Check if path exists
        if not path.exists() and command != "create":
            raise ToolError(
                f"The path {path} does not exist. Please provide a valid path."
            )
        if path.exists() and command == "create":
            raise ToolError(
                f"File already exists at: {path}. Cannot overwrite files using command `create`."
            )
        # Check if the path points to a directory
        if path.is_dir():
            if command != "view":
                raise ToolError(
                    f"The path {path} is a directory and only the `view` command can be used on directories"
                )
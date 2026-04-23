async def execute(
        self,
        action: str,
        file_path: Optional[str] = None,
        file_contents: Optional[str] = None,
        old_str: Optional[str] = None,
        new_str: Optional[str] = None,
        permissions: Optional[str] = "644",
        **kwargs,
    ) -> ToolResult:
        """
        Execute a file operation in the sandbox environment.
        Args:
            action: The file operation to perform
            file_path: Path to the file relative to /workspace
            file_contents: Content to write to the file
            old_str: Text to be replaced (for str_replace)
            new_str: Replacement text (for str_replace)
            permissions: File permissions in octal format
        Returns:
            ToolResult with the operation's output or error
        """
        async with asyncio.Lock():
            try:
                # File creation
                if action == "create_file":
                    if not file_path or not file_contents:
                        return self.fail_response(
                            "file_path and file_contents are required for create_file"
                        )
                    return await self._create_file(
                        file_path, file_contents, permissions
                    )

                # String replacement
                elif action == "str_replace":
                    if not file_path or not old_str or not new_str:
                        return self.fail_response(
                            "file_path, old_str, and new_str are required for str_replace"
                        )
                    return await self._str_replace(file_path, old_str, new_str)

                # Full file rewrite
                elif action == "full_file_rewrite":
                    if not file_path or not file_contents:
                        return self.fail_response(
                            "file_path and file_contents are required for full_file_rewrite"
                        )
                    return await self._full_file_rewrite(
                        file_path, file_contents, permissions
                    )

                # File deletion
                elif action == "delete_file":
                    if not file_path:
                        return self.fail_response(
                            "file_path is required for delete_file"
                        )
                    return await self._delete_file(file_path)

                else:
                    return self.fail_response(f"Unknown action: {action}")

            except Exception as e:
                logger.error(f"Error executing file action: {e}")
                return self.fail_response(f"Error executing file action: {e}")
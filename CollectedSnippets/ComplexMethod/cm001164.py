def _validate_file_access(
        self,
        blob_name: str,
        user_id: str | None = None,
        graph_exec_id: str | None = None,
    ) -> None:
        """
        Validate that a user can access a specific file path.

        Args:
            blob_name: The blob path in GCS
            user_id: The requesting user ID (optional)
            graph_exec_id: The requesting graph execution ID (optional)

        Raises:
            PermissionError: If access is denied
        """

        # Normalize the path to prevent path traversal attacks
        normalized_path = os.path.normpath(blob_name)

        # Ensure the normalized path doesn't contain any path traversal attempts
        if ".." in normalized_path or normalized_path.startswith("/"):
            raise PermissionError("Invalid file path: path traversal detected")

        # Split into components and validate each part
        path_parts = normalized_path.split("/")

        # Validate path structure: must start with "uploads/"
        if not path_parts or path_parts[0] != "uploads":
            raise PermissionError("Invalid file path: must be under uploads/")

        # System uploads (uploads/system/*) can be accessed by anyone for backwards compatibility
        if len(path_parts) >= 2 and path_parts[1] == "system":
            return

        # User-specific uploads (uploads/users/{user_id}/*) require matching user_id
        if len(path_parts) >= 2 and path_parts[1] == "users":
            if not user_id or len(path_parts) < 3:
                raise PermissionError(
                    "User ID required to access user files"
                    if not user_id
                    else "Invalid user file path format"
                )

            file_owner_id = path_parts[2]
            # Validate user_id format (basic validation) - no need to check ".." again since we already did
            if not file_owner_id or "/" in file_owner_id:
                raise PermissionError("Invalid user ID in path")

            if file_owner_id != user_id:
                raise PermissionError(
                    f"Access denied: file belongs to user {file_owner_id}"
                )
            return

        # Execution-specific uploads (uploads/executions/{graph_exec_id}/*) require matching graph_exec_id
        if len(path_parts) >= 2 and path_parts[1] == "executions":
            if not graph_exec_id or len(path_parts) < 3:
                raise PermissionError(
                    "Graph execution ID required to access execution files"
                    if not graph_exec_id
                    else "Invalid execution file path format"
                )

            file_exec_id = path_parts[2]
            # Validate execution_id format (basic validation) - no need to check ".." again since we already did
            if not file_exec_id or "/" in file_exec_id:
                raise PermissionError("Invalid execution ID in path")

            if file_exec_id != graph_exec_id:
                raise PermissionError(
                    f"Access denied: file belongs to execution {file_exec_id}"
                )
            return

        # Legacy uploads directory (uploads/*) - allow for backwards compatibility with warning
        # Note: We already validated it starts with "uploads/" above, so this is guaranteed to match
        logger.warning(f"[CloudStorage] Accessing legacy upload path: {blob_name}")
        return
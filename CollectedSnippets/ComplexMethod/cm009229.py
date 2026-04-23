def _handle_glob_search(
        self,
        pattern: str,
        path: str,
        state: AnthropicToolsState,
    ) -> str:
        """Handle glob search operation.

        Args:
            pattern: The glob pattern to match files against.
            path: The directory to search in.
            state: The current agent state.

        Returns:
            Newline-separated list of matching file paths, sorted by modification
                time (most recently modified first).

                Returns `'No files found'` if no matches.
        """
        # Normalize base path
        base_path = path if path.startswith("/") else "/" + path

        # Get files from state
        files = cast("dict[str, Any]", state.get(self.state_key, {}))

        # Match files
        matches = []
        for file_path, file_data in files.items():
            if file_path.startswith(base_path):
                # Get relative path from base
                if base_path == "/":
                    relative = file_path[1:]  # Remove leading /
                elif file_path == base_path:
                    relative = Path(file_path).name
                elif file_path.startswith(base_path + "/"):
                    relative = file_path[len(base_path) + 1 :]
                else:
                    continue

                # Match against pattern
                # Handle ** pattern which requires special care
                # PurePosixPath.match doesn't match single-level paths
                # against **/pattern
                is_match = PurePosixPath(relative).match(pattern)
                if not is_match and pattern.startswith("**/"):
                    # Also try matching without the **/ prefix for files in base dir
                    is_match = PurePosixPath(relative).match(pattern[3:])

                if is_match:
                    matches.append((file_path, file_data["modified_at"]))

        if not matches:
            return "No files found"

        # Sort by modification time
        matches.sort(key=lambda x: x[1], reverse=True)
        file_paths = [path for path, _ in matches]

        return "\n".join(file_paths)
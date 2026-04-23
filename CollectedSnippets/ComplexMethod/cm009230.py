def _handle_grep_search(
        self,
        pattern: str,
        path: str,
        include: str | None,
        output_mode: str,
        state: AnthropicToolsState,
    ) -> str:
        """Handle grep search operation.

        Args:
            pattern: The regular expression pattern to search for in file contents.
            path: The directory to search in.
            include: File pattern to filter (e.g., `'*.js'`, `'*.{ts,tsx}'`).
            output_mode: Output format.
            state: The current agent state.

        Returns:
            Search results formatted according to `output_mode`.

                Returns `'No matches found'` if no results.
        """
        # Normalize base path
        base_path = path if path.startswith("/") else "/" + path

        # Compile regex pattern (for validation)
        try:
            regex = re.compile(pattern)
        except re.error as e:
            return f"Invalid regex pattern: {e}"

        if include and not _is_valid_include_pattern(include):
            return "Invalid include pattern"

        # Search files
        files = cast("dict[str, Any]", state.get(self.state_key, {}))
        results: dict[str, list[tuple[int, str]]] = {}

        for file_path, file_data in files.items():
            if not file_path.startswith(base_path):
                continue

            # Check include filter
            if include:
                basename = Path(file_path).name
                if not _match_include_pattern(basename, include):
                    continue

            # Search file content
            for line_num, line in enumerate(file_data["content"], 1):
                if regex.search(line):
                    if file_path not in results:
                        results[file_path] = []
                    results[file_path].append((line_num, line))

        if not results:
            return "No matches found"

        # Format output based on mode
        return self._format_grep_results(results, output_mode)
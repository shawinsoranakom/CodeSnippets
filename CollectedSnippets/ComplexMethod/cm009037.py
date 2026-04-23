def glob_search(pattern: str, path: str = "/") -> str:
            """Fast file pattern matching tool that works with any codebase size.

            Supports glob patterns like `**/*.js` or `src/**/*.ts`.

            Returns matching file paths sorted by modification time.

            Use this tool when you need to find files by name patterns.

            Args:
                pattern: The glob pattern to match files against.
                path: The directory to search in. If not specified, searches from root.

            Returns:
                Newline-separated list of matching file paths, sorted by modification
                time (most recently modified first). Returns `'No files found'` if no
                matches.
            """
            try:
                base_full = self._validate_and_resolve_path(path)
            except ValueError:
                return "No files found"

            if not base_full.exists() or not base_full.is_dir():
                return "No files found"

            # Use pathlib glob
            matching: list[tuple[str, str]] = []
            for match in base_full.glob(pattern):
                if match.is_file():
                    # Convert to virtual path
                    virtual_path = "/" + str(match.relative_to(self.root_path))
                    stat = match.stat()
                    modified_at = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    matching.append((virtual_path, modified_at))

            if not matching:
                return "No files found"

            file_paths = [p for p, _ in matching]
            return "\n".join(file_paths)
def _python_search(
        self, pattern: str, base_path: str, include: str | None
    ) -> dict[str, list[tuple[int, str]]]:
        """Search using Python regex (fallback)."""
        try:
            base_full = self._validate_and_resolve_path(base_path)
        except ValueError:
            return {}

        if not base_full.exists():
            return {}

        regex = re.compile(pattern)
        results: dict[str, list[tuple[int, str]]] = {}

        # Walk directory tree
        for file_path in base_full.rglob("*"):
            if not file_path.is_file():
                continue

            # Check include filter
            if include and not _match_include_pattern(file_path.name, include):
                continue

            # Skip files that are too large
            if file_path.stat().st_size > self.max_file_size_bytes:
                continue

            try:
                content = file_path.read_text()
            except (UnicodeDecodeError, PermissionError):
                continue

            # Search content
            for line_num, line in enumerate(content.splitlines(), 1):
                if regex.search(line):
                    virtual_path = "/" + str(file_path.relative_to(self.root_path))
                    if virtual_path not in results:
                        results[virtual_path] = []
                    results[virtual_path].append((line_num, line))

        return results
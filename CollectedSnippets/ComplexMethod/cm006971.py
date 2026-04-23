def check_file_patterns(file_path: str | Path, patterns: str) -> bool:
        """Check if a file matches the given patterns.

        Args:
            file_path: Path to the file to check
            patterns: Comma-separated list of glob patterns

        Returns:
            bool: True if file should be included, False if excluded
        """
        # Handle empty or whitespace-only patterns
        if not patterns or patterns.isspace():
            return True

        path_str = str(file_path)
        file_name = Path(path_str).name
        pattern_list: list[str] = [pattern.strip() for pattern in patterns.split(",") if pattern.strip()]

        # If no valid patterns after stripping, treat as include all
        if not pattern_list:
            return True

        # Process exclusion patterns first
        for pattern in pattern_list:
            if pattern.startswith("!"):
                # For exclusions, match against both full path and filename
                exclude_pattern = pattern[1:]
                if fnmatch(path_str, exclude_pattern) or fnmatch(file_name, exclude_pattern):
                    return False

        # Then check inclusion patterns
        include_patterns = [p for p in pattern_list if not p.startswith("!")]
        # If no include patterns, treat as include all
        if not include_patterns:
            return True

        # For inclusions, match against both full path and filename
        return any(fnmatch(path_str, pattern) or fnmatch(file_name, pattern) for pattern in include_patterns)
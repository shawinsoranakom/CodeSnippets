def search_in_files(
        self,
        pattern: str,
        directory: str | Path = ".",
        file_pattern: str = "*",
        max_results: int = 100,
    ) -> str:
        """Search for a pattern in files.

        Args:
            pattern (str): The regex pattern to search for
            directory (str): The directory to search in
            file_pattern (str): Glob pattern to filter files
            max_results (int): Maximum number of results

        Returns:
            str: Matching lines with file names and line numbers
        """
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise CommandExecutionError(f"Invalid regex pattern: {e}")

        results = []
        files = self.workspace.list_files(directory)

        for file_path in files:
            if not fnmatch.fnmatch(str(file_path), file_pattern):
                continue

            try:
                file = self.workspace.open_file(file_path, binary=True)
                content = decode_textual_file(
                    file, os.path.splitext(file_path)[1], logger
                )

                for line_num, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        results.append(f"{file_path}:{line_num}: {line.strip()}")
                        if len(results) >= max_results:
                            break

                if len(results) >= max_results:
                    break
            except Exception:
                # Skip files that can't be read as text
                continue

        if not results:
            return f"No matches found for pattern '{pattern}'"

        header = f"Found {len(results)} match(es)"
        if len(results) >= max_results:
            header += f" (limited to {max_results})"
        header += ":"

        return header + "\n" + "\n".join(results)
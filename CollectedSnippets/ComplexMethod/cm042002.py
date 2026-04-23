def search_file(self, search_term: str, file_path: Optional[str] = None) -> str:
        """Searches for search_term in file. If file is not provided, searches in the current open file.

        Args:
            search_term: str: The term to search for.
            file_path: str | None: The path to the file to search.
        """
        if file_path is None:
            file_path = self.current_file
        else:
            file_path = self._try_fix_path(file_path)
        if file_path is None:
            raise FileNotFoundError("No file specified or open. Use the open_file function first.")
        if not file_path.is_file():
            raise FileNotFoundError(f"File {file_path} not found")

        matches = []
        with file_path.open() as file:
            for i, line in enumerate(file, 1):
                if search_term in line:
                    matches.append((i, line.strip()))
        res_list = []
        if matches:
            res_list.append(f'[Found {len(matches)} matches for "{search_term}" in {file_path}]')
            for match in matches:
                res_list.append(f"Line {match[0]}: {match[1]}")
            res_list.append(f'[End of matches for "{search_term}" in {file_path}]')
        else:
            res_list.append(f'[No matches found for "{search_term}" in {file_path}]')

        extra = {"type": "search", "symbol": search_term, "lines": [i[0] - 1 for i in matches]} if matches else None
        self.resource.report(file_path, "path", extra=extra)
        return "\n".join(res_list)
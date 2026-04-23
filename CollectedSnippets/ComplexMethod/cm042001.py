def search_dir(self, search_term: str, dir_path: str = "./") -> str:
        """Searches for search_term in all files in dir. If dir is not provided, searches in the current directory.

        Args:
            search_term: str: The term to search for.
            dir_path: str: The path to the directory to search.
        """
        dir_path = self._try_fix_path(dir_path)
        if not dir_path.is_dir():
            raise FileNotFoundError(f"Directory {dir_path} not found")
        matches = []
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.startswith("."):
                    continue
                file_path = Path(root) / file
                with file_path.open("r", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        if search_term in line:
                            matches.append((file_path, line_num, line.strip()))

        if not matches:
            return f'No matches found for "{search_term}" in {dir_path}'

        num_matches = len(matches)
        num_files = len(set(match[0] for match in matches))

        if num_files > 100:
            return f'More than {num_files} files matched for "{search_term}" in {dir_path}. Please narrow your search.'

        res_list = [f'[Found {num_matches} matches for "{search_term}" in {dir_path}]']
        for file_path, line_num, line in matches:
            res_list.append(f"{file_path} (Line {line_num}): {line}")
        res_list.append(f'[End of matches for "{search_term}" in {dir_path}]')
        return "\n".join(res_list)
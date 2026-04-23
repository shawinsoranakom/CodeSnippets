def open_file(
        self, path: Union[Path, str], line_number: Optional[int] = 1, context_lines: Optional[int] = None
    ) -> str:
        """Opens the file at the given path in the editor. If line_number is provided, the window will be moved to include that line.
        It only shows the first 100 lines by default! Max `context_lines` supported is 2000, use `scroll up/down`
        to view the file if you want to see more.

        Args:
            path: str: The path to the file to open, preferred absolute path.
            line_number: int | None = 1: The line number to move to. Defaults to 1.
            context_lines: int | None = 100: Only shows this number of lines in the context window (usually from line 1), with line_number as the center (if possible). Defaults to 100.
        """
        if context_lines is None:
            context_lines = self.window

        path = self._try_fix_path(path)

        if not path.is_file():
            raise FileNotFoundError(f"File {path} not found")

        self.current_file = path
        with path.open() as file:
            total_lines = max(1, sum(1 for _ in file))

        if not isinstance(line_number, int) or line_number < 1 or line_number > total_lines:
            raise ValueError(f"Line number must be between 1 and {total_lines}")
        self.current_line = line_number

        # Override WINDOW with context_lines
        if context_lines is None or context_lines < 1:
            context_lines = self.window

        output = self._cur_file_header(path, total_lines)
        output += self._print_window(path, self.current_line, self._clamp(context_lines, 1, 2000))
        self.resource.report(path, "path")
        return output
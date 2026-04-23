def split(
        self,
        separator: str = "\n",
        *,
        include_separator: bool = False,
        allow_blank: bool = False,
    ) -> Lines:
        """Split rich text in to lines, preserving styles.

        Args:
            separator (str, optional): String to split on. Defaults to "\\\\n".
            include_separator (bool, optional): Include the separator in the lines. Defaults to False.
            allow_blank (bool, optional): Return a blank line if the text ends with a separator. Defaults to False.

        Returns:
            List[RichText]: A list of rich text, one per line of the original.
        """
        assert separator, "separator must not be empty"

        text = self.plain
        if separator not in text:
            return Lines([self.copy()])

        if include_separator:
            lines = self.divide(
                match.end() for match in re.finditer(re.escape(separator), text)
            )
        else:

            def flatten_spans() -> Iterable[int]:
                for match in re.finditer(re.escape(separator), text):
                    start, end = match.span()
                    yield start
                    yield end

            lines = Lines(
                line for line in self.divide(flatten_spans()) if line.plain != separator
            )

        if not allow_blank and text.endswith(separator):
            lines.pop()

        return lines
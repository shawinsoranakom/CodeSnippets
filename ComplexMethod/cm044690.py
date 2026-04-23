def highlight(
        self,
        code: str,
        line_range: Optional[Tuple[Optional[int], Optional[int]]] = None,
    ) -> Text:
        """Highlight code and return a Text instance.

        Args:
            code (str): Code to highlight.
            line_range(Tuple[int, int], optional): Optional line range to highlight.

        Returns:
            Text: A text instance containing highlighted syntax.
        """

        base_style = self._get_base_style()
        justify: JustifyMethod = (
            "default" if base_style.transparent_background else "left"
        )

        text = Text(
            justify=justify,
            style=base_style,
            tab_size=self.tab_size,
            no_wrap=not self.word_wrap,
        )
        _get_theme_style = self._theme.get_style_for_token

        lexer = self.lexer or self.default_lexer

        if lexer is None:
            text.append(code)
        else:
            if line_range:
                # More complicated path to only stylize a portion of the code
                # This speeds up further operations as there are less spans to process
                line_start, line_end = line_range

                def line_tokenize() -> Iterable[Tuple[Any, str]]:
                    """Split tokens to one per line."""
                    assert lexer  # required to make MyPy happy - we know lexer is not None at this point

                    for token_type, token in lexer.get_tokens(code):
                        while token:
                            line_token, new_line, token = token.partition("\n")
                            yield token_type, line_token + new_line

                def tokens_to_spans() -> Iterable[Tuple[str, Optional[Style]]]:
                    """Convert tokens to spans."""
                    tokens = iter(line_tokenize())
                    line_no = 0
                    _line_start = line_start - 1 if line_start else 0

                    # Skip over tokens until line start
                    while line_no < _line_start:
                        try:
                            _token_type, token = next(tokens)
                        except StopIteration:
                            break
                        yield (token, None)
                        if token.endswith("\n"):
                            line_no += 1
                    # Generate spans until line end
                    for token_type, token in tokens:
                        yield (token, _get_theme_style(token_type))
                        if token.endswith("\n"):
                            line_no += 1
                            if line_end and line_no >= line_end:
                                break

                text.append_tokens(tokens_to_spans())

            else:
                text.append_tokens(
                    (token, _get_theme_style(token_type))
                    for token_type, token in lexer.get_tokens(code)
                )
            if self.background_color is not None:
                text.stylize(f"on {self.background_color}")

        if self._stylized_ranges:
            self._apply_stylized_ranges(text)

        return text
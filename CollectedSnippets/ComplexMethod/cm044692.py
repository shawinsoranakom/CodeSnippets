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
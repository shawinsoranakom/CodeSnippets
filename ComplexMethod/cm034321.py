def tokeniter(self, *args, **kwargs) -> t.Iterator[t.Tuple[int, str, str]]:
        """Pre-escape backslashes in expression ({{ }}) raw string constants before Jinja's Lexer.wrap() can interpret them as ASCII escape sequences."""
        token_stream = super().tokeniter(*args, **kwargs)

        # if we have no context, Jinja's doing a nested compile at runtime (eg, import/include); historically, no backslash escaping is performed
        if not (tcc := _TemplateCompileContext.current(optional=True)) or not tcc.escape_backslashes:
            yield from token_stream
            return

        in_variable = False

        for token in token_stream:
            token_type = token[1]

            if token_type == TOKEN_VARIABLE_BEGIN:
                in_variable = True
            elif token_type == TOKEN_VARIABLE_END:
                in_variable = False
            elif in_variable and token_type == TOKEN_STRING:
                token = token[0], token_type, token[2].replace('\\', '\\\\')

            yield token
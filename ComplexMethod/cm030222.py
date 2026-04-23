def _find_keyword_typos(self):
        assert self._is_syntax_error
        try:
            import _suggestions
        except ImportError:
            _suggestions = None

        # Only try to find keyword typos if there is no custom message
        if self.msg != "invalid syntax" and "Perhaps you forgot a comma" not in self.msg:
            return

        if not self._exc_metadata:
            return

        line, offset, source = self._exc_metadata
        end_line = int(self.lineno) if self.lineno is not None else 0
        lines = None
        from_filename = False

        if source is None:
            if self.filename:
                try:
                    with open(self.filename) as f:
                        lines = f.read().splitlines()
                except Exception:
                    line, end_line, offset = 0,1,0
                else:
                    from_filename = True
            lines = lines if lines is not None else self.text.splitlines()
        else:
            lines = source.splitlines()

        error_code = lines[line -1 if line > 0 else 0:end_line]
        error_code = textwrap.dedent('\n'.join(error_code))

        # Do not continue if the source is too large
        if len(error_code) > 1024:
            return

        # If the original code doesn't raise SyntaxError, we can't validate
        # that a keyword replacement actually fixes anything
        try:
            codeop.compile_command(error_code, symbol="exec", flags=codeop.PyCF_ONLY_AST)
        except SyntaxError:
            pass  # Good - the original code has a syntax error we might fix
        else:
            return  # Original code compiles or is incomplete - can't validate fixes

        error_lines = error_code.splitlines()
        tokens = tokenize.generate_tokens(io.StringIO(error_code).readline)
        tokens_left_to_process = 10
        import difflib
        for token in tokens:
            start, end = token.start, token.end
            if token.type != tokenize.NAME:
                continue
            # Only consider NAME tokens on the same line as the error
            the_end = end_line if line == 0 else end_line + 1
            if from_filename and token.start[0]+line != the_end:
                continue
            wrong_name = token.string
            if wrong_name in keyword.kwlist:
                continue

            # Limit the number of valid tokens to consider to not spend
            # to much time in this function
            tokens_left_to_process -= 1
            if tokens_left_to_process < 0:
                break
            # Limit the number of possible matches to try
            max_matches = 3
            matches = []
            if _suggestions is not None:
                suggestion = _suggestions._generate_suggestions(keyword.kwlist, wrong_name)
                if suggestion:
                    matches.append(suggestion)
            matches.extend(difflib.get_close_matches(wrong_name, keyword.kwlist, n=max_matches, cutoff=0.5))
            matches = matches[:max_matches]
            for suggestion in matches:
                if not suggestion or suggestion == wrong_name:
                    continue
                # Try to replace the token with the keyword
                the_lines = error_lines.copy()
                the_line = the_lines[start[0] - 1][:]
                chars = list(the_line)
                chars[token.start[1]:token.end[1]] = suggestion
                the_lines[start[0] - 1] = ''.join(chars)
                code = '\n'.join(the_lines)

                # Check if it works
                try:
                    codeop.compile_command(code, symbol="exec", flags=codeop.PyCF_ONLY_AST)
                except SyntaxError:
                    continue

                # Keep token.line but handle offsets correctly
                self.text = token.line
                self.offset = token.start[1] + 1
                self.end_offset = token.end[1] + 1
                self.lineno = start[0]
                self.end_lineno = end[0]
                self.msg = f"invalid syntax. Did you mean '{suggestion}'?"
                return
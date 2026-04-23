def _handle_unexpected_token(cls, exc: UnexpectedToken, script_lines: List[str]) -> ErrorDetail:
        """Handle UnexpectedToken errors"""
        line = exc.line
        column = exc.column

        # Get context lines
        source_line = script_lines[line - 1] if 0 < line <= len(script_lines) else ""
        line_before = script_lines[line - 2] if line > 1 and line <= len(script_lines) + 1 else None
        line_after = script_lines[line] if 0 < line < len(script_lines) else None

        # Determine error type and suggestions
        if exc.token.type == 'CLICK' and 'THEN' in str(exc.expected):
            code = cls.ERROR_CODES["missing_then"]
            message = "Missing 'THEN' keyword after IF condition"
            suggestions = [
                Suggestion(
                    "Add 'THEN' after the condition",
                    source_line.replace("CLICK", "THEN CLICK") if source_line else None
                )
            ]
        elif exc.token.type == '$END':
            code = cls.ERROR_CODES["missing_endproc"]
            message = "Unexpected end of script"
            suggestions = [
                Suggestion("Check for missing ENDPROC"),
                Suggestion("Ensure all procedures are properly closed")
            ]
        elif 'RPAR' in str(exc.expected):
            code = cls.ERROR_CODES["missing_paren"]
            message = "Missing closing parenthesis ')'"
            suggestions = [
                Suggestion("Add closing parenthesis at the end of the condition")
            ]
        elif 'COMMA' in str(exc.expected):
            code = cls.ERROR_CODES["missing_comma"]
            message = "Missing comma ',' in command"
            suggestions = [
                Suggestion("Add comma between arguments")
            ]
        else:
            # Check if this might be missing backticks
            if exc.token.type == 'NAME' and 'BACKTICK_STRING' in str(exc.expected):
                code = cls.ERROR_CODES["missing_backticks"]
                message = "Selector must be wrapped in backticks"
                suggestions = [
                    Suggestion(
                        "Wrap the selector in backticks",
                        f"`{exc.token.value}`"
                    )
                ]
            else:
                code = cls.ERROR_CODES["syntax_error"]
                message = f"Unexpected '{exc.token.value}'"
                if exc.expected:
                    expected_list = [str(e) for e in exc.expected if not str(e).startswith('_')][:3]
                    if expected_list:
                        message += f". Expected: {', '.join(expected_list)}"
                suggestions = []

        return ErrorDetail(
            type=ErrorType.SYNTAX,
            code=code,
            severity=Severity.ERROR,
            message=message,
            line=line,
            column=column,
            source_line=source_line,
            line_before=line_before,
            line_after=line_after,
            suggestions=suggestions
        )
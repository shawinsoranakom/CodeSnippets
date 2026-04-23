def from_exception(cls, exc: Exception, script: Union[str, List[str]]) -> 'C4AScriptError':
        """Create C4AScriptError from another exception"""
        script_text = script if isinstance(script, str) else '\n'.join(script)
        script_lines = script_text.split('\n')

        if isinstance(exc, UnexpectedToken):
            # Extract line and column from UnexpectedToken
            line = exc.line
            column = exc.column

            # Get the problematic line
            if 0 < line <= len(script_lines):
                problem_line = script_lines[line - 1]
                marker = " " * (column - 1) + "^"

                details = f"\nCode:\n  {problem_line}\n  {marker}\n"

                # Improve error message based on context
                if exc.token.type == 'CLICK' and 'THEN' in str(exc.expected):
                    message = "Missing 'THEN' keyword after IF condition"
                elif exc.token.type == '$END':
                    message = "Unexpected end of script. Check for missing ENDPROC or incomplete commands"
                elif 'RPAR' in str(exc.expected):
                    message = "Missing closing parenthesis ')'"
                elif 'COMMA' in str(exc.expected):
                    message = "Missing comma ',' in command"
                else:
                    message = f"Unexpected '{exc.token}'"
                    if exc.expected:
                        expected_list = [str(e) for e in exc.expected if not e.startswith('_')]
                        if expected_list:
                            message += f". Expected: {', '.join(expected_list[:3])}"

                details += f"Token: {exc.token.type} ('{exc.token.value}')"
            else:
                message = str(exc)
                details = None

            return cls(message, line, column, "Syntax Error", details)

        elif isinstance(exc, UnexpectedCharacters):
            # Extract line and column
            line = exc.line
            column = exc.column

            if 0 < line <= len(script_lines):
                problem_line = script_lines[line - 1]
                marker = " " * (column - 1) + "^"

                details = f"\nCode:\n  {problem_line}\n  {marker}\n"
                message = f"Invalid character or unexpected text at position {column}"
            else:
                message = str(exc)
                details = None

            return cls(message, line, column, "Syntax Error", details)

        elif isinstance(exc, ValueError):
            # Handle runtime errors like undefined procedures
            message = str(exc)

            # Try to find which line caused the error
            if "Unknown procedure" in message:
                proc_name = re.search(r"'([^']+)'", message)
                if proc_name:
                    proc_name = proc_name.group(1)
                    for i, line in enumerate(script_lines, 1):
                        if proc_name in line and not line.strip().startswith('PROC'):
                            details = f"\nCode:\n  {line.strip()}\n\nMake sure the procedure '{proc_name}' is defined with PROC...ENDPROC"
                            return cls(f"Undefined procedure '{proc_name}'", i, None, "Runtime Error", details)

            return cls(message, None, None, "Runtime Error", None)

        else:
            # Generic error
            return cls(str(exc), None, None, "Compilation Error", None)
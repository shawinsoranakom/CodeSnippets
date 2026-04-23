def _format_parse_errors(
        self,
        errors: list[Exception],
        tool_calls: Optional[list[AssistantToolCall]],
        functions: Optional[list[CompletionModelFunction]],
    ) -> str:
        """Format parse errors with helpful context about what was provided vs expected.

        Args:
            errors: List of parsing/validation errors.
            tool_calls: The tool calls that were parsed (may have validation errors).
            functions: List of available functions for schema lookup.

        Returns:
            Formatted error string with context.
        """
        formatted_errors = []

        for error in errors:
            if isinstance(error, InvalidFunctionCallError):
                # Build informative error message with context
                error_parts = [str(error)]

                # Show what arguments were provided
                if error.arguments:
                    args_str = ", ".join(
                        f'"{k}": {repr(v)}' for k, v in error.arguments.items()
                    )
                    error_parts.append(f"\nYou provided: {{{args_str}}}")
                else:
                    error_parts.append("\nYou provided: (no arguments)")

                # Show expected schema if we have the function definition
                if functions:
                    func = next(
                        (f for f in functions if f.name == error.name),
                        None,
                    )
                    if func and func.parameters:
                        params_info = []
                        for name, param in func.parameters.items():
                            req = "required" if param.required else "optional"
                            type_str = param.type.value if param.type else "any"
                            params_info.append(f'"{name}": {type_str} ({req})')
                        error_parts.append(
                            f"\nExpected parameters: {{{', '.join(params_info)}}}"
                        )

                formatted_errors.append("".join(error_parts))
            else:
                # For non-tool-call errors, just use the standard format
                formatted_errors.append(f"{error.__class__.__name__}: {error}")

        return "\n\n".join(formatted_errors)
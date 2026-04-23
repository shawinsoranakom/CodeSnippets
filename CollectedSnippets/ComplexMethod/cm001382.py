def _get_tool_error_message(
        self,
        tool_call: AssistantToolCall,
        tool_call_errors: list,
        functions: Optional[list[CompletionModelFunction]] = None,
    ) -> str:
        """Get the error message for a failed tool call.

        Args:
            tool_call: The tool call that failed.
            tool_call_errors: List of validation errors for tool calls.
            functions: List of available functions for schema lookup.

        Returns:
            An appropriate error message for the tool result.
        """
        if not tool_call_errors:
            return "Not executed because parsing of your last message failed"

        # Find matching error for this specific tool call
        matching_error = next(
            (err for err in tool_call_errors if err.name == tool_call.function.name),
            None,
        )
        if not matching_error:
            return "Not executed: validation failed"

        # Build informative error message with context
        error_parts = [str(matching_error)]

        # Show what arguments were provided
        provided_args = tool_call.function.arguments
        if provided_args:
            args_str = ", ".join(f'"{k}": {repr(v)}' for k, v in provided_args.items())
            error_parts.append(f"\nYou provided: {{{args_str}}}")
        else:
            error_parts.append("\nYou provided: (no arguments)")

        # Show expected schema if we have the function definition
        if functions:
            func = next(
                (f for f in functions if f.name == tool_call.function.name),
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

        return "".join(error_parts)
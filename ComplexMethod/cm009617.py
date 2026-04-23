def _filter_injected_args(self, tool_input: dict) -> dict:
        """Filter out injected tool arguments from the input dictionary.

        Injected arguments are those annotated with `InjectedToolArg` or its
        subclasses, or arguments in `FILTERED_ARGS` like `run_manager` and callbacks.

        Args:
            tool_input: The tool input dictionary to filter.

        Returns:
            A filtered dictionary with injected arguments removed.
        """
        # Start with filtered args from the constant
        filtered_keys = set[str](FILTERED_ARGS)

        # Add injected args from function signature (e.g., ToolRuntime parameters)
        filtered_keys.update(self._injected_args_keys)

        # If we have an args_schema, use it to identify injected args
        # Skip if args_schema is a dict (JSON Schema) as it's not a Pydantic model
        if self.args_schema is not None and not isinstance(self.args_schema, dict):
            try:
                annotations = get_all_basemodel_annotations(self.args_schema)
                for field_name, field_type in annotations.items():
                    if _is_injected_arg_type(field_type):
                        filtered_keys.add(field_name)
            except Exception:
                # If we can't get annotations, just use FILTERED_ARGS
                _logger.debug(
                    "Failed to get args_schema annotations for filtering.",
                    exc_info=True,
                )

        # Filter out the injected keys from tool_input
        return {k: v for k, v in tool_input.items() if k not in filtered_keys}
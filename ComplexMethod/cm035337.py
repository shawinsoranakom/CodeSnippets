def handle_action_deprecated_args(args: dict[str, Any]) -> dict[str, Any]:
    # keep_prompt has been deprecated in https://github.com/OpenHands/OpenHands/pull/4881
    if 'keep_prompt' in args:
        args.pop('keep_prompt')

    # task_completed has been deprecated - remove it from args to maintain backward compatibility
    if 'task_completed' in args:
        args.pop('task_completed')

    # Handle translated_ipython_code deprecation
    if 'translated_ipython_code' in args:
        code = args.pop('translated_ipython_code')

        # Check if it's a file_editor call using a prefix check for efficiency
        file_editor_prefix = 'print(file_editor(**'
        if (
            code is not None
            and code.startswith(file_editor_prefix)
            and code.endswith('))')
        ):
            try:
                # Extract and evaluate the dictionary string
                import ast

                # Extract the dictionary string between the prefix and the closing parentheses
                dict_str = code[len(file_editor_prefix) : -2]  # Remove prefix and '))'
                file_args = ast.literal_eval(dict_str)

                # Update args with the extracted file editor arguments
                args.update(file_args)
            except (ValueError, SyntaxError):
                # If parsing fails, just remove the translated_ipython_code
                pass

        if args.get('command') == 'view':
            args.pop(
                'command'
            )  # "view" will be translated to FileReadAction which doesn't have a command argument

    return args
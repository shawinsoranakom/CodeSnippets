def _merge_function_call_content(existing_call: FunctionCallContent, new_chunk: FunctionCallContent) -> None:
        """Helper to merge partial argument chunks from new_chunk into existing_call."""
        if isinstance(existing_call.arguments, str) and isinstance(new_chunk.arguments, str):
            existing_call.arguments += new_chunk.arguments
        elif isinstance(existing_call.arguments, dict) and isinstance(new_chunk.arguments, dict):
            existing_call.arguments.update(new_chunk.arguments)
        elif not existing_call.arguments or existing_call.arguments in ("{}", ""):
            # If existing had no arguments yet, just take the new one
            existing_call.arguments = new_chunk.arguments
        else:
            # If there's a mismatch (str vs dict), handle as needed
            warnings.warn("Mismatch in argument types during merge. Existing arguments retained.", stacklevel=2)

        # Optionally update name/function_name if newly provided
        if new_chunk.name:
            existing_call.name = new_chunk.name
        if new_chunk.plugin_name:
            existing_call.plugin_name = new_chunk.plugin_name
        if new_chunk.function_name:
            existing_call.function_name = new_chunk.function_name
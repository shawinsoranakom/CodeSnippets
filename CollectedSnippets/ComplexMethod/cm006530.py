def _simplify_output_content(content: Any, output_type: str) -> Any:
    """Simplify output content for output nodes.

    For message types, extracts plain text from nested structures.
    For data/dataframe types, extracts the actual data value.
    For other types, returns content as-is.

    Args:
        content: The raw content
        output_type: The output type

    Returns:
        Simplified content
    """
    if not isinstance(content, dict):
        return content

    if output_type in {"message", "text"}:
        text = _extract_text_from_message(content)
        return text if text is not None else content

    if output_type == "data":
        # For data types, try multiple path combinations in order
        # This allows flexibility for different component output structures
        data_paths = [
            ("result", "message"),  # Standard: {'result': {'message': {...}}}
            ("results", "message"),  # Plural variant: {'results': {'message': {...}}}
        ]
        for path in data_paths:
            result_data = _extract_nested_value(content, *path)
            if result_data is not None:
                return result_data
    # TODO: Future scope - Add dataframe-specific extraction logic
    # The following code is commented out pending further requirements analysis:
    if output_type == "dataframe":
        # For dataframe types, try multiple path combinations in order
        dataframe_paths = [
            ("results", "message"),  # Plural: {'results': {'message': {...}}}
            ("result", "message"),  # Singular fallback: {'result': {'message': {...}}}
            ("run_sql_query", "message"),  # SQL component specific
        ]
        for path in dataframe_paths:
            dataframe_data = _extract_nested_value(content, *path)
            if dataframe_data is not None:
                return dataframe_data

    return content
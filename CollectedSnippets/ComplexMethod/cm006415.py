def data_to_text_list(template: str, data: Data | list[Data]) -> tuple[list[str], list[Data]]:
    """Format text from Data objects using a template string.

    This function processes Data objects and formats their content using a template string.
    It handles various data structures and ensures consistent text formatting across different
    input types.

    Key Features:
    - Supports single Data object or list of Data objects
    - Handles nested dictionaries and extracts text from various locations
    - Uses safe string formatting with fallback for missing keys
    - Preserves original Data objects in output

    Args:
        template: Format string with placeholders (e.g., "Hello {text}")
                 Placeholders are replaced with values from Data objects
        data: Either a single Data object or a list of Data objects to format
              Each object can contain text, dictionaries, or nested data

    Returns:
        A tuple containing:
        - List[str]: Formatted strings based on the template
        - List[Data]: Original Data objects in the same order

    Raises:
        ValueError: If template is None
        TypeError: If template is not a string

    Examples:
        >>> result = data_to_text_list("Hello {text}", Data(text="world"))
        >>> assert result == (["Hello world"], [Data(text="world")])

        >>> result = data_to_text_list(
        ...     "{name} is {age}",
        ...     Data(data={"name": "Alice", "age": 25})
        ... )
        >>> assert result == (["Alice is 25"], [Data(data={"name": "Alice", "age": 25})])
    """
    if data is None:
        return [], []

    if template is None:
        msg = "Template must be a string, but got None."
        raise ValueError(msg)

    if not isinstance(template, str):
        msg = f"Template must be a string, but got {type(template)}"
        raise TypeError(msg)

    formatted_text: list[str] = []
    processed_data: list[Data] = []

    data_list = [data] if isinstance(data, Data) else data

    data_objects = [item if isinstance(item, Data) else Data(text=str(item)) for item in data_list]

    for data_obj in data_objects:
        format_dict = {}

        if isinstance(data_obj.data, dict):
            format_dict.update(data_obj.data)

            if isinstance(data_obj.data.get("data"), dict):
                format_dict.update(data_obj.data["data"])

            elif format_dict.get("error"):
                format_dict["text"] = format_dict["error"]

        format_dict["data"] = data_obj.data

        safe_dict = defaultdict(str, format_dict)

        try:
            formatted_text.append(template.format_map(safe_dict))
            processed_data.append(data_obj)
        except ValueError as e:
            msg = f"Error formatting template: {e!s}"
            raise ValueError(msg) from e

    return formatted_text, processed_data
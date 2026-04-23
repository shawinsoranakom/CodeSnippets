def split_and_parse_json_objects(json_string):
    """
    Splits a JSON string which is a list of objects and tries to parse each object.

    Parameters:
    json_string (str): A string representation of a list of JSON objects, e.g., '[{...}, {...}, ...]'.

    Returns:
    tuple: A tuple containing two lists:
        - First list contains all successfully parsed JSON objects.
        - Second list contains the string representations of all segments that couldn't be parsed.
    """
    # Trim the leading '[' and trailing ']'
    if json_string.startswith("[") and json_string.endswith("]"):
        json_string = json_string[1:-1].strip()

    # Split the string into segments that look like individual JSON objects
    segments = []
    depth = 0
    start_index = 0

    for i, char in enumerate(json_string):
        if char == "{":
            if depth == 0:
                start_index = i
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                segments.append(json_string[start_index : i + 1])

    # Try parsing each segment
    parsed_objects = []
    unparsed_segments = []

    for segment in segments:
        try:
            obj = json.loads(segment)
            parsed_objects.append(obj)
        except json.JSONDecodeError:
            unparsed_segments.append(segment)

    return parsed_objects, unparsed_segments
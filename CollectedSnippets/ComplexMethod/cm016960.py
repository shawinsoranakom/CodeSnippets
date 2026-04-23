def recraft_multipart_parser(
    data,
    parent_key=None,
    formatter: type[callable] | None = None,
    converted_to_check: list[list] | None = None,
    is_list: bool = False,
    return_mode: str = "formdata",  # "dict" | "formdata"
) -> dict | aiohttp.FormData:
    """
    Formats data such that multipart/form-data will work with aiohttp library when both files and data are present.

    The OpenAI client that Recraft uses has a bizarre way of serializing lists:

    It does NOT keep track of indeces of each list, so for background_color, that must be serialized as:
        'background_color[rgb][]' = [0, 0, 255]
    where the array is assigned to a key that has '[]' at the end, to signal it's an array.

    This has the consequence of nested lists having the exact same key, forcing arrays to merge; all colors inputs fall under the same key:
        if 1 color  -> 'controls[colors][][rgb][]' = [0, 0, 255]
        if 2 colors -> 'controls[colors][][rgb][]' = [0, 0, 255, 255, 0, 0]
        if 3 colors -> 'controls[colors][][rgb][]' = [0, 0, 255, 255, 0, 0, 0, 255, 0]
        etc.
    Whoever made this serialization up at OpenAI added the constraint that lists must be of uniform length on objects of same 'type'.
    """
    # Modification of a function that handled a different type of multipart parsing, big ups:
    # https://gist.github.com/kazqvaizer/4cebebe5db654a414132809f9f88067b

    def handle_converted_lists(item, parent_key, lists_to_check=list[list]):
        # if list already exists, just extend list with data
        for check_list in lists_to_check:
            for conv_tuple in check_list:
                if conv_tuple[0] == parent_key and isinstance(conv_tuple[1], list):
                    conv_tuple[1].append(formatter(item))
                    return True
        return False

    if converted_to_check is None:
        converted_to_check = []

    effective_mode = return_mode if parent_key is None else "dict"
    if formatter is None:
        formatter = lambda v: v  # Multipart representation of value

    if not isinstance(data, dict):
        # if list already exists, just extend list with data
        added = handle_converted_lists(data, parent_key, converted_to_check)
        if added:
            return {}
        # otherwise if is_list, create new list with data
        if is_list:
            return {parent_key: [formatter(data)]}
        # return new key with data
        return {parent_key: formatter(data)}

    converted = []
    next_check = [converted]
    next_check.extend(converted_to_check)

    for key, value in data.items():
        current_key = key if parent_key is None else f"{parent_key}[{key}]"
        if isinstance(value, dict):
            converted.extend(recraft_multipart_parser(value, current_key, formatter, next_check).items())
        elif isinstance(value, list):
            for ind, list_value in enumerate(value):
                iter_key = f"{current_key}[]"
                converted.extend(
                    recraft_multipart_parser(list_value, iter_key, formatter, next_check, is_list=True).items()
                )
        else:
            converted.append((current_key, formatter(value)))

    if effective_mode == "formdata":
        fd = aiohttp.FormData()
        for k, v in dict(converted).items():
            if isinstance(v, list):
                for item in v:
                    fd.add_field(k, str(item))
            else:
                fd.add_field(k, str(v))
        return fd
    return dict(converted)
def to_lower_camel_case(snake_case_str):
    """Converts snake_case to lowerCamelCase.

    Example:
        foo_bar -> fooBar
        fooBar -> foobar
    """
    words = snake_case_str.split("_")
    if len(words) > 1:
        capitalized = [w.title() for w in words]
        capitalized[0] = words[0]
        return "".join(capitalized)
    else:
        return snake_case_str
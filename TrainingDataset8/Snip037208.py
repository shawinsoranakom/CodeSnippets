def to_upper_camel_case(snake_case_str):
    """Converts snake_case to UpperCamelCase.
    Example:
        foo_bar -> FooBar
    """
    return "".join(map(str.title, snake_case_str.split("_")))
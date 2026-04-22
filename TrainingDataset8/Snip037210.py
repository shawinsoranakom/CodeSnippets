def to_snake_case(camel_case_str):
    """Converts UpperCamelCase and lowerCamelCase to snake_case.

    Examples:
        fooBar -> foo_bar
        BazBang -> baz_bang
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camel_case_str)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
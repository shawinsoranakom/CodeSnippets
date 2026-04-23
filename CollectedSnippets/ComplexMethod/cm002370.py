def sort_objects(objects: list[Any], key: Callable[[Any], str] | None = None) -> list[Any]:
    """
    Sort a list of objects following the rules of isort (all uppercased first, camel-cased second and lower-cased
    last).

    Args:
        objects (`List[Any]`):
            The list of objects to sort.
        key (`Callable[[Any], str]`, *optional*):
            A function taking an object as input and returning a string, used to sort them by alphabetical order.
            If not provided, will default to noop (so a `key` must be provided if the `objects` are not of type string).

    Returns:
        `List[Any]`: The sorted list with the same elements as in the inputs
    """

    # If no key is provided, we use a noop.
    def noop(x):
        return x

    if key is None:
        key = noop
    # Constants are all uppercase, they go first.
    constants = [obj for obj in objects if key(obj).isupper()]
    # Classes are not all uppercase but start with a capital, they go second.
    classes = [obj for obj in objects if key(obj)[0].isupper() and not key(obj).isupper()]
    # Functions begin with a lowercase, they go last.
    functions = [obj for obj in objects if not key(obj)[0].isupper()]

    # Then we sort each group.
    key1 = ignore_underscore_and_lowercase(key)
    return sorted(constants, key=key1) + sorted(classes, key=key1) + sorted(functions, key=key1)
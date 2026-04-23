def _retrieve_ref(path: str, schema: dict) -> list | dict:
    """Retrieve a referenced object from a JSON schema using a path.

    Resolves JSON schema references (e.g., `'#/definitions/MyType'`) by traversing the
    schema structure.

    Args:
        path: Reference path starting with `'#'` (e.g., `'#/definitions/MyType'`).
        schema: The JSON schema dictionary to search in.

    Returns:
        A deep copy of the referenced object (dict or list).

    Raises:
        ValueError: If the path does not start with `'#'`.
        KeyError: If the reference path is not found in the schema.
    """
    components = path.split("/")
    if components[0] != "#":
        msg = (
            "ref paths are expected to be URI fragments, meaning they should start "
            "with #."
        )
        raise ValueError(msg)
    out: list | dict = schema
    for component in components[1:]:
        if component in out:
            if isinstance(out, list):
                msg = f"Reference '{path}' not found."
                raise KeyError(msg)
            out = out[component]
        elif component.isdigit():
            index = int(component)
            if (isinstance(out, list) and 0 <= index < len(out)) or (
                isinstance(out, dict) and index in out
            ):
                out = out[index]
            else:
                msg = f"Reference '{path}' not found."
                raise KeyError(msg)
        else:
            msg = f"Reference '{path}' not found."
            raise KeyError(msg)
    return deepcopy(out)
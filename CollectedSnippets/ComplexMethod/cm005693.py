def fetch__all__(file_content) -> list[str]:
    """
    Returns the content of the __all__ variable in the file content.
    Returns None if not defined, otherwise returns a list of strings.
    """

    if "__all__" not in file_content:
        return []

    start_index = None
    lines = file_content.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("__all__"):
            start_index = index

    # There is no line starting with `__all__`
    if start_index is None:
        return []

    lines = lines[start_index:]

    if not lines[0].startswith("__all__"):
        raise ValueError(
            "fetch__all__ accepts a list of lines, with the first line being the __all__ variable declaration"
        )

    # __all__ is defined on a single line
    if lines[0].endswith("]"):
        return [obj.strip("\"' ") for obj in lines[0].split("=")[1].strip(" []").split(",")]

    # __all__ is defined on multiple lines
    else:
        _all: list[str] = []
        for __all__line_index in range(1, len(lines)):
            if lines[__all__line_index].strip() == "]":
                return _all
            else:
                _all.append(lines[__all__line_index].strip("\"', "))

        return _all
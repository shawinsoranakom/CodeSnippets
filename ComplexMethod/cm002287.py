def find_code_in_transformers(
    object_name: str, base_path: str | None = None, return_indices: bool = False
) -> str | tuple[list[str], int, int]:
    """
    Find and return the source code of an object.

    Args:
        object_name (`str`):
            The name of the object we want the source code of.
        base_path (`str`, *optional*):
            The path to the base folder where files are checked. If not set, it will be set to `TRANSFORMERS_PATH`.
        return_indices(`bool`, *optional*, defaults to `False`):
            If `False`, will only return the code (as a string), otherwise it will also return the whole lines of the
            file where the object specified by `object_name` is defined, together the start/end indices of the block in
            the file that defines the object.

    Returns:
        `Union[str, Tuple[List[str], int, int]]`: If `return_indices=False`, only the source code of the object will be
        returned. Otherwise, it also returns the whole lines of the file where the object specified by `object_name` is
        defined, together the start/end indices of the block in the file that defines the object.
    """
    parts = object_name.split(".")
    i = 0

    # We can't set this as the default value in the argument, otherwise `CopyCheckTester` will fail, as it uses a
    # patched temp directory.
    if base_path is None:
        base_path = TRANSFORMERS_PATH

    # Detail: the `Copied from` statement is originally designed to work with the last part of `TRANSFORMERS_PATH`,
    # (which is `transformers`). The same should be applied for `MODEL_TEST_PATH`. However, its last part is `models`
    # (to only check and search in it) which is a bit confusing. So we keep the copied statement starting with
    # `tests.models.` and change it to `tests` here.
    if base_path == MODEL_TEST_PATH:
        base_path = "tests"

    # First let's find the module where our object lives.
    module = parts[i]
    while i < len(parts) and not os.path.isfile(os.path.join(base_path, f"{module}.py")):
        i += 1
        if i < len(parts):
            module = os.path.join(module, parts[i])
    if i >= len(parts):
        raise ValueError(
            f"`object_name` should begin with the name of a module of transformers but got {object_name}."
        )

    with open(os.path.join(base_path, f"{module}.py"), "r", encoding="utf-8", newline="\n") as f:
        lines = f.readlines()

    # Now let's find the class / func in the code!
    indent = ""
    line_index = 0
    for name in parts[i + 1 :]:
        while (
            line_index < len(lines) and re.search(rf"^{indent}(class|def)\s+{name}(\(|\:)", lines[line_index]) is None
        ):
            line_index += 1
        # find the target specified in the current level in `parts` -> increase `indent` so we can search the next
        indent += "    "
        # the index of the first line in the (currently found) block *body*
        line_index += 1

    if line_index >= len(lines):
        raise ValueError(f" {object_name} does not match any function or class in {module}.")

    # `indent` is already one level deeper than the (found) class/func block's definition header

    # We found the beginning of the class / func, now let's find the end (when the indent diminishes).
    # `start_index` is the index of the class/func block's definition header
    start_index = line_index - 1
    end_index = find_block_end(lines, start_index, len(indent))

    code = "".join(lines[start_index:end_index])
    return (code, (lines, start_index, end_index)) if return_indices else code
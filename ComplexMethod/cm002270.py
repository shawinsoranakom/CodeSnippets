def fix_docstring(obj: Any, old_doc_args: str, new_doc_args: str):
    """
    Fixes the docstring of an object by replacing its arguments documentation by the one matched with the signature.

    Args:
        obj (`Any`):
            The object whose dostring we are fixing.
        old_doc_args (`str`):
            The current documentation of the parameters of `obj` in the docstring (as returned by
            `match_docstring_with_signature`).
        new_doc_args (`str`):
            The documentation of the parameters of `obj` matched with its signature (as returned by
            `match_docstring_with_signature`).
    """
    # Read the docstring in the source code and make sure we have the right part of the docstring
    source, line_number = inspect.getsourcelines(obj)

    # Get to the line where we start documenting arguments
    idx = 0
    while idx < len(source) and _re_args.search(source[idx]) is None:
        idx += 1

    if idx == len(source):
        # Args are not defined in the docstring of this object. This can happen when the docstring is inherited.
        # In this case, we are not trying to fix it on the child object.
        return

    # Get to the line where we stop documenting arguments
    indent = find_indent(source[idx])
    idx += 1
    start_idx = idx
    while idx < len(source) and (len(source[idx].strip()) == 0 or find_indent(source[idx]) > indent):
        idx += 1

    idx -= 1
    while len(source[idx].strip()) == 0:
        idx -= 1
    idx += 1

    # `old_doc_args` is built from `obj.__doc__`, which may have
    # different indentation than the raw source from `inspect.getsourcelines`.
    # We use `inspect.cleandoc` to remove indentation uniformly from both
    # strings before comparing them.
    source_args_as_str = "".join(source[start_idx:idx])
    if inspect.cleandoc(source_args_as_str) != inspect.cleandoc(old_doc_args):
        # Args are not fully defined in the docstring of this object
        obj_file = find_source_file(obj)
        actual_args_section = source_args_as_str.rstrip()
        raise ValueError(
            f"Cannot fix docstring of {obj.__name__} in {obj_file} because the argument section in the source code "
            f"does not match the expected format. This usually happens when:\n"
            f"1. The argument section is not properly indented\n"
            f"2. The argument section contains unexpected formatting\n"
            f"3. The docstring parsing failed to correctly identify the argument boundaries\n\n"
            f"Expected argument section:\n{repr(old_doc_args)}\n\n"
            f"Actual argument section found:\n{repr(actual_args_section)}\n\n"
        )

    obj_file = find_source_file(obj)
    with open(obj_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace content
    lines = content.split("\n")
    prev_line_indentation = find_indent(lines[line_number + start_idx - 2])
    # Now increase the indentation of every line in new_doc_args by prev_line_indentation
    new_doc_args = "\n".join([f"{' ' * prev_line_indentation}{line}" for line in new_doc_args.split("\n")])

    lines = lines[: line_number + start_idx - 1] + [new_doc_args] + lines[line_number + idx - 1 :]

    print(f"Fixing the docstring of {obj.__name__} in {obj_file}.")
    with open(obj_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
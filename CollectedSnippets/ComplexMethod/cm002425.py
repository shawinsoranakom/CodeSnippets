def preprocess_string(string, skip_cuda_tests):
    """Prepare a docstring or a `.md` file to be run by doctest.

    The argument `string` would be the whole file content if it is a `.md` file. For a python file, it would be one of
    its docstring. In each case, it may contain multiple python code examples. If `skip_cuda_tests` is `True` and a
    cuda stuff is detective (with a heuristic), this method will return an empty string so no doctest will be run for
    `string`.
    """
    codeblock_pattern = r"(```(?:python|py)\s*\n\s*>>> )(.*?```)"
    codeblocks = re.split(codeblock_pattern, string, flags=re.DOTALL)
    is_cuda_found = False
    for i, codeblock in enumerate(codeblocks):
        if "load_dataset(" in codeblock and "# doctest: +IGNORE_RESULT" not in codeblock:
            codeblocks[i] = re.sub(r"(>>> .*load_dataset\(.*)", r"\1 # doctest: +IGNORE_RESULT", codeblock)
        if (
            (">>>" in codeblock or "..." in codeblock)
            and re.search(r"cuda|to\(0\)|device=0", codeblock)
            and skip_cuda_tests
        ):
            is_cuda_found = True
            break

    modified_string = ""
    if not is_cuda_found:
        modified_string = "".join(codeblocks)

    return modified_string
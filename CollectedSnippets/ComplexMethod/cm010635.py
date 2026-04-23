def get_type_line(source):
    """Try to find the line containing a comment with the type annotation."""
    type_comment = "# type:"

    lines = source.split("\n")
    lines = list(enumerate(lines))
    type_lines = list(filter(lambda line: type_comment in line[1], lines))
    # `type: ignore` comments may be needed in JIT'ed functions for mypy, due
    # to the hack in torch/_VF.py.

    # An ignore type comment can be of following format:
    #   1) type: ignore
    #   2) type: ignore[rule-code]
    # This ignore statement must be at the end of the line

    # adding an extra backslash before the space, to avoid triggering
    # one of the checks in .github/workflows/lint.yml
    type_pattern = re.compile("# type:\\ ignore(\\[[a-zA-Z-]+\\])?$")
    type_lines = list(filter(lambda line: not type_pattern.search(line[1]), type_lines))

    if len(type_lines) == 0:
        # Catch common typo patterns like extra spaces, typo in 'ignore', etc.
        wrong_type_pattern = re.compile("#[\t ]*type[\t ]*(?!: ignore(\\[.*\\])?$):")
        wrong_type_lines = list(
            filter(lambda line: wrong_type_pattern.search(line[1]), lines)
        )
        if len(wrong_type_lines) > 0:
            raise RuntimeError(
                "The annotation prefix in line "
                + str(wrong_type_lines[0][0])
                + " is probably invalid.\nIt must be '# type:'"
                + "\nSee PEP 484 (https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code)"
                + "\nfor examples"
            )
        return None
    elif len(type_lines) == 1:
        # Only 1 type line, quit now
        return type_lines[0][1].strip()

    # Parse split up argument types according to PEP 484
    # https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code
    return_line = None
    parameter_type_lines = []
    for line_num, line in type_lines:
        if "# type: (...) -> " in line:
            return_line = (line_num, line)
            break
        elif type_comment in line:
            parameter_type_lines.append(line)
    if return_line is None:
        raise RuntimeError(
            "Return type line '# type: (...) -> ...' not found on multiline "
            "type annotation\nfor type lines:\n"
            + "\n".join([line[1] for line in type_lines])
            + "\n(See PEP 484 https://www.python.org/dev/peps/pep-0484/#suggested-syntax-for-python-2-7-and-straddling-code)"
        )

    def get_parameter_type(line):
        item_type = line[line.find(type_comment) + len(type_comment) :]
        return item_type.strip()

    types = map(get_parameter_type, parameter_type_lines)
    parameter_types = ", ".join(types)

    return return_line[1].replace("...", parameter_types)
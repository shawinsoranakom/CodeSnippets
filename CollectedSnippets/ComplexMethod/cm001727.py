def parse_args_from_docstring_by_indentation(docstring):
    # This util is used in pipeline tests, to extract the argument names from a google-format docstring
    # to compare them against the Hub specification for that task. It uses indentation levels as a primary
    # source of truth, so these have to be correct!
    docstring = dedent(docstring)
    lines_by_indent = [
        (len(line) - len(line.lstrip()), line.strip()) for line in docstring.split("\n") if line.strip()
    ]
    args_lineno = None
    args_indent = None
    args_end = None
    for lineno, (indent, line) in enumerate(lines_by_indent):
        if line == "Args:":
            args_lineno = lineno
            args_indent = indent
            continue
        elif args_lineno is not None and indent == args_indent:
            args_end = lineno
            break
    if args_lineno is None:
        raise ValueError("No args block to parse!")
    elif args_end is None:
        args_block = lines_by_indent[args_lineno + 1 :]
    else:
        args_block = lines_by_indent[args_lineno + 1 : args_end]
    outer_indent_level = min(line[0] for line in args_block)
    outer_lines = [line for line in args_block if line[0] == outer_indent_level]
    arg_names = [re.match(r"(\w+)\W", line[1]).group(1) for line in outer_lines]
    return arg_names
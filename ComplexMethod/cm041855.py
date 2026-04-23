def add_active_line_prints(code):
    """
    Add print statements indicating line numbers to a python string.
    """
    # Replace newlines and comments with pass statements, so the line numbers are accurate (ast will remove them otherwise)
    code_lines = code.split("\n")
    in_multiline_string = False
    for i in range(len(code_lines)):
        line = code_lines[i]
        if '"""' in line or "'''" in line:
            in_multiline_string = not in_multiline_string
        if not in_multiline_string and (line.strip().startswith("#") or line == ""):
            whitespace = len(line) - len(line.lstrip(" "))
            code_lines[i] = " " * whitespace + "pass"
    processed_code = "\n".join(code_lines)
    try:
        tree = ast.parse(processed_code)
    except:
        # If you can't parse the processed version, try the unprocessed version before giving up
        tree = ast.parse(code)
    transformer = AddLinePrints()
    new_tree = transformer.visit(tree)
    return ast.unparse(new_tree)
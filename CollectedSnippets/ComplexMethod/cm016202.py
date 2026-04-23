def preprocess(
    input_text: str, variables: dict[str, Any], input_path: str = "codegen"
) -> str:
    input_lines = input_text.splitlines()
    python_lines = []

    blank_lines = 0

    last_indent = ""

    # List of tuples (total_index, python_indent)
    indent_stack = [("", "")]

    # Indicates whether this is the first line inside Python
    # code block (i.e. for, while, if, elif, else)
    python_block_start = True
    for input_line in input_lines:
        if input_line == "":
            blank_lines += 1
            continue
        # Skip lint markers.
        if "LINT" in input_line:
            continue

        input_indent = extract_leading_whitespace(input_line)
        if python_block_start:
            if not input_indent.startswith(last_indent):
                raise AssertionError("input_indent must start with last_indent")
            extra_python_indent = input_indent[len(last_indent) :]
            python_indent = indent_stack[-1][1] + extra_python_indent
            indent_stack.append((input_indent, python_indent))
            if not input_indent.startswith(indent_stack[-1][0]):
                raise AssertionError("input_indent must start with indent_stack top")
        else:
            while not input_indent.startswith(indent_stack[-1][0]):
                del indent_stack[-1]
        python_block_start = False

        python_indent = indent_stack[-1][1]
        stripped_input_line = input_line.strip()
        if stripped_input_line.startswith("$") and not stripped_input_line.startswith(
            "${"
        ):
            if stripped_input_line.endswith(":"):
                python_block_start = True
            while blank_lines != 0:
                python_lines.append(python_indent + "print(file=OUT_STREAM)")
                blank_lines -= 1
            python_lines.append(python_indent + stripped_input_line.replace("$", ""))
        else:
            if not input_line.startswith(python_indent):
                raise AssertionError("input_line must start with python_indent")
            while blank_lines != 0:
                python_lines.append(python_indent + "print(file=OUT_STREAM)")
                blank_lines -= 1
            python_lines.append(
                python_indent
                + f"print({escape(input_line[len(python_indent) :])}, file=OUT_STREAM)"
            )
        last_indent = input_indent

    while blank_lines != 0:
        # pyrefly: ignore [unbound-name]
        python_lines.append(python_indent + "print(file=OUT_STREAM)")
        blank_lines -= 1

    exec_globals = dict(variables)
    output_stream = io.StringIO()
    exec_globals["OUT_STREAM"] = output_stream

    python_bytecode = compile("\n".join(python_lines), input_path, "exec")
    exec(python_bytecode, exec_globals)

    return output_stream.getvalue()
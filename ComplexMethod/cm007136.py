def _parse_code(self, code: str) -> tuple[list[dict], list[dict]]:
        parsed_code = ast.parse(code)
        lines = code.split("\n")
        classes = []
        functions = []
        for node in parsed_code.body:
            if isinstance(node, ast.ClassDef):
                class_lines = lines[node.lineno - 1 : node.end_lineno]
                class_lines[-1] = class_lines[-1][: node.end_col_offset]
                class_lines[0] = class_lines[0][node.col_offset :]
                classes.append(
                    {
                        "name": node.name,
                        "code": class_lines,
                    }
                )
                continue

            if not isinstance(node, ast.FunctionDef):
                continue

            func = {"name": node.name, "args": []}
            for arg in node.args.args:
                if arg.lineno != arg.end_lineno:
                    msg = "Multiline arguments are not supported"
                    raise ValueError(msg)

                func_arg = {
                    "name": arg.arg,
                    "annotation": None,
                }

                for default in node.args.defaults:
                    if (
                        arg.lineno > default.lineno
                        or arg.col_offset > default.col_offset
                        or (
                            arg.end_lineno is not None
                            and default.end_lineno is not None
                            and arg.end_lineno < default.end_lineno
                        )
                        or (
                            arg.end_col_offset is not None
                            and default.end_col_offset is not None
                            and arg.end_col_offset < default.end_col_offset
                        )
                    ):
                        continue

                    if isinstance(default, ast.Name):
                        func_arg["default"] = default.id
                    elif isinstance(default, ast.Constant):
                        func_arg["default"] = str(default.value) if default.value is not None else None

                if arg.annotation:
                    annotation_line = lines[arg.annotation.lineno - 1]
                    annotation_line = annotation_line[: arg.annotation.end_col_offset]
                    annotation_line = annotation_line[arg.annotation.col_offset :]
                    func_arg["annotation"] = annotation_line
                    if isinstance(func_arg["annotation"], str) and func_arg["annotation"].count("=") > 0:
                        func_arg["annotation"] = "=".join(func_arg["annotation"].split("=")[:-1]).strip()
                if isinstance(func["args"], list):
                    func["args"].append(func_arg)
            functions.append(func)

        return classes, functions
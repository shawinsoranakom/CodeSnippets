def _should_show_carets(self, start_offset, end_offset, all_lines, anchors):
        with suppress(SyntaxError, ImportError):
            import ast
            tree = ast.parse('\n'.join(all_lines))
            if not tree.body:
                return False
            statement = tree.body[0]
            value = None
            def _spawns_full_line(value):
                return (
                    value.lineno == 1
                    and value.end_lineno == len(all_lines)
                    and value.col_offset == start_offset
                    and value.end_col_offset == end_offset
                )
            match statement:
                case ast.Return(value=ast.Call()):
                    if isinstance(statement.value.func, ast.Name):
                        value = statement.value
                case ast.Assign(value=ast.Call()):
                    if (
                        len(statement.targets) == 1 and
                        isinstance(statement.targets[0], ast.Name)
                    ):
                        value = statement.value
            if value is not None and _spawns_full_line(value):
                return False
        if anchors:
            return True
        if all_lines[0][:start_offset].lstrip() or all_lines[-1][end_offset:].rstrip():
            return True
        return False
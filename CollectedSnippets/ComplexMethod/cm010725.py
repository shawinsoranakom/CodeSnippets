def visit_Call(self, node: ast.Call) -> None:
                triton_func_names = ("capture_triton", "wrap_triton")
                if isinstance(node.func, ast.Attribute):
                    attr = node.func
                    if isinstance(attr.value, ast.Attribute):
                        if (
                            isinstance(attr.value.value, ast.Name)
                            and attr.value.value.id == "torch"
                            and attr.value.attr == "_library"
                            and attr.attr in triton_func_names
                        ):
                            if node.args and isinstance(node.args[0], ast.Name):
                                self.triton_kernels.append(node.args[0].id)
                        elif (
                            isinstance(attr.value.value, ast.Attribute)
                            and isinstance(attr.value.value.value, ast.Name)
                            and attr.value.value.value.id == "torch"
                            and attr.value.value.attr == "ops"
                        ):
                            self.called_functions.append(
                                f"{attr.value.attr}::{attr.attr}"
                            )
                # Catch capture_triton, wrap_triton that's been
                # imported directly
                elif isinstance(node.func, ast.Name):
                    if node.func.id in triton_func_names:
                        if node.args and isinstance(node.args[0], ast.Name):
                            self.triton_kernels.append(node.args[0].id)
                    else:
                        # track regular function calls for recursive analysis
                        self.called_functions.append(node.func.id)

                self.generic_visit(node)
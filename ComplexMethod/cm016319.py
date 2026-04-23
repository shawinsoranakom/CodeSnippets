def _check_with_statement(self, node: ast.With, msg_prefix: str) -> None:
        for item in node.items:
            ctx_expr = item.context_expr
            if isinstance(ctx_expr, ast.Call):
                func = ctx_expr.func
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "device"
                    and isinstance(func.value, ast.Name)
                    and func.value.id == "torch"
                    and ctx_expr.args
                    and isinstance(ctx_expr.args[0], ast.Constant)
                    # pyrefly: ignore [not-iterable, unsupported-operation]
                    and any(bias in ctx_expr.args[0].value for bias in DEVICE_BIAS)
                ):
                    self.record(
                        ctx_expr,
                        f"{msg_prefix} `with torch.device('{ctx_expr.args[0].value}')`, suggest to use torch.device(GPU_TYPE)",
                    )
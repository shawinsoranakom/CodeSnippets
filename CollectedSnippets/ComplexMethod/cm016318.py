def _check_device_methods(self, subnode: ast.Call, msg_prefix: str) -> None:
        func = subnode.func
        if not isinstance(func, ast.Attribute):
            return
        method_name = func.attr
        if method_name in DEVICE_BIAS:
            self.record(
                subnode,
                f"{msg_prefix} .{method_name}(), suggest to use .to(GPU_TYPE)",
            )
        elif method_name == "to" and subnode.args:
            arg = subnode.args[0]
            if isinstance(arg, ast.Constant) and any(
                # pyrefly: ignore [not-iterable, unsupported-operation]
                bias in arg.value
                for bias in DEVICE_BIAS
            ):
                self.record(
                    subnode,
                    f"{msg_prefix} .to('{arg.value}'), suggest to use .to(GPU_TYPE)",
                )
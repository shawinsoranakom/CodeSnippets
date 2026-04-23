def _check_keyword_device(self, subnode: ast.keyword, msg_prefix: str) -> None:
        if subnode.arg != "device":
            return
        val = subnode.value
        if isinstance(val, ast.Constant) and any(
            # pyrefly: ignore [not-iterable, unsupported-operation]
            bias in val.value
            for bias in DEVICE_BIAS
        ):
            self.record(
                subnode,
                f"{msg_prefix} device='{val.value}', suggest to use device=GPU_TYPE",
            )
        elif isinstance(val, ast.Call):
            if (
                isinstance(val.func, ast.Attribute)
                and val.func.attr == "device"
                and len(val.args) > 0
                and isinstance(val.args[0], ast.Constant)
                # pyrefly: ignore [not-iterable, unsupported-operation]
                and any(bias in val.args[0].value for bias in DEVICE_BIAS)
            ):
                self.record(
                    val,
                    f"{msg_prefix} torch.device('{val.args[0].value}'), suggest to use torch.device(GPU_TYPE)",
                )
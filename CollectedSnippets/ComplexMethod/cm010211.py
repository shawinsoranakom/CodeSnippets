def rank_input(inp) -> tuple[int, str | None, int]:
        idx, (_arg, spec) = inp
        if not isinstance(spec, InputSpec):
            raise AssertionError(f"expected InputSpec, got {type(spec).__name__}")
        if spec.type == "user_input":
            return 5, None, idx
        elif spec.type == "parameter":
            return 1, spec.parameter.parameter_name, idx
        elif spec.type == "buffer":
            return 2, spec.buffer.buffer_name, idx
        elif spec.type == "tensor_constant":
            return 3, spec.tensor_constant.tensor_constant_name, idx
        elif spec.type == "custom_obj":
            return 4, spec.custom_obj.custom_obj_name, idx
        elif spec.type == "token":
            return 0, None, idx
        elif spec.type == "constant_input":
            return 6, spec.constant_input.name, idx
        else:
            raise AssertionError(f"Unknown input type: {spec}")
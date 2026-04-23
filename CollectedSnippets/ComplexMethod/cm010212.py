def rank_output(out) -> tuple[int, str | None, int]:
        idx, (_arg, spec) = out
        if not isinstance(spec, OutputSpec):
            raise AssertionError(f"expected OutputSpec, got {type(spec).__name__}")
        if spec.type == "user_output":
            return 4, None, idx
        elif spec.type == "loss_output":
            return 4, None, idx
        elif spec.type == "parameter_mutation":
            return 1, spec.parameter_mutation.parameter_name, idx
        elif spec.type == "buffer_mutation":
            return 2, spec.buffer_mutation.buffer_name, idx
        elif spec.type == "gradient_to_parameter":
            return 5, spec.gradient_to_parameter.parameter_name, idx
        elif spec.type == "gradient_to_user_input":
            return 6, None, idx
        elif spec.type == "user_input_mutation":
            return 3, None, idx
        elif spec.type == "token":
            return 0, None, idx
        else:
            raise AssertionError(f"Unknown output type: {spec}")
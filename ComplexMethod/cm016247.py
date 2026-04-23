def emit_any_requires_grad() -> list[str]:
        extra_condition = ""
        if info and info.output_differentiability_conditions:
            if len(info.output_differentiability_conditions) != 1:
                raise AssertionError(
                    f"expected 1 output_differentiability_condition, got {len(info.output_differentiability_conditions)}"
                )
            extra_condition = f"_any_requires_grad &= ({info.output_differentiability_conditions[0]});"
        names_of_args_with_derivatives = [arg.name for arg in args_with_derivatives]
        if is_inplace_foreach and info is not None:
            for i, arg in enumerate(names_of_args_with_derivatives):
                for f_arg, r_arg in inplace_foreacharg2refarg.items():
                    if arg == r_arg.name:
                        names_of_args_with_derivatives[i] = f_arg.name
        return [
            SETUP_ANY_REQUIRES_GRAD.substitute(
                args_with_derivatives=names_of_args_with_derivatives,
                extra_differentiability_conditions=extra_condition,
            )
        ]
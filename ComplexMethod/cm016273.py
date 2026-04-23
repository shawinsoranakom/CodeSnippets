def emit_derivative(
        derivative: Derivative,
        args_with_derivatives: Sequence[Binding],
    ) -> tuple[bool, str]:
        formula = derivative.formula
        var_names = derivative.var_names

        if len(var_names) == 1:
            checks_any_grad_defined = False
            if "not_implemented" not in formula:
                matching_args = [
                    arg for arg in args_with_derivatives if arg.name == var_names[0]
                ]
                if len(matching_args) == 1:
                    # We can add undefined grad support if the input variable is a Tensor
                    arg = matching_args[0]
                    if isinstance(arg.argument, Argument) and str(
                        arg.argument.type
                    ) in ("Tensor", "Tensor?"):
                        formula = "any_grad_defined ? (" + formula + ") : Tensor()"
                        checks_any_grad_defined = True
            if info.name.startswith("_foreach_"):
                derivative_template = DERIVATIVE_SINGLE_FOREACH
            else:
                derivative_template = DERIVATIVE_SINGLE
            return (
                checks_any_grad_defined,
                derivative_template.substitute(
                    name=var_names[0],
                    derivative=formula,
                    idx=input_name_to_idx[var_names[0]],
                ),
            )

        else:
            if "grad_input_mask" in formula:
                masks = [
                    f"needs_input_grad[{input_name_to_idx[name]}],"
                    for name in var_names
                ]
                grad_input_mask = GRAD_INPUT_MASK.substitute(
                    n=len(var_names), masks=masks
                )
            else:
                grad_input_mask = ""
            needs_input_grad = [
                f"needs_input_grad[{input_name_to_idx[name]}]" for name in var_names
            ]
            needs_input_grad = " || ".join(needs_input_grad)
            copy_ranges: list[str] = []
            for i, n in enumerate(var_names):
                copy_ranges.append(
                    DERIVATIVE_MULTI_COPY_RANGE.substitute(
                        name=n, i=i, idx=input_name_to_idx[n]
                    )
                )
            return False, DERIVATIVE_MULTI.substitute(
                needs_input_grad=needs_input_grad,
                copy_ranges=copy_ranges,
                derivative=formula,
                grad_input_mask=grad_input_mask,
            )
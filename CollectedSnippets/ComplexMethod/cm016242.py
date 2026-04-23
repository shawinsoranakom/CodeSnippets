def setup_derivative(differentiable_inputs: list[DifferentiableInput]) -> list[str]:
        body: list[str] = []
        if is_out_fn:
            # For out functions, ensure that no input or output requires grad
            body.append(DECLARE_GRAD_FN.substitute(op="Node"))
            body.append(
                SETUP_NONE_REQUIRES_GRAD.substitute(
                    base_name=base_name,
                    args_to_check=[arg.name for arg in differentiable_inputs],
                )
            )
            body.append(
                SETUP_NONE_REQUIRES_GRAD.substitute(
                    base_name=base_name,
                    args_to_check=[arg.name for arg in differentiable_outputs],
                )
            )
            return body

        op = info.op if info is not None and info.has_derivatives else "NotImplemented"
        setup = []
        if not is_inplace_foreach:
            setup.extend(
                ASSIGN_GRAD_FN.substitute(
                    op=op,
                    op_ctor=""
                    if info is not None and info.has_derivatives
                    else f'"{cpp.name(f.func)}"',
                    args_with_derivatives=[arg.name for arg in args_with_derivatives],
                ).split("\n")
            )
        else:
            # note(crcrpar): Assuming in-place foreach function's self_arg is always TensorList.
            list_like_arg = "self"
            args = [arg.name for arg in args_with_derivatives]
            for i, arg in enumerate(args):
                if is_inplace_foreach and info is not None:
                    if arg in refargname2inplace_foreacharg:
                        foreach_arg = refargname2inplace_foreacharg[arg]
                        args[i] = foreach_arg.name + (
                            "[i]" if isinstance(foreach_arg.type, ListType) else ""
                        )
                else:
                    if arg == list_like_arg:
                        args[i] = arg + "[i]"
            setup.extend(
                ASSIGN_VECTOR_OF_GRAD_FN.substitute(
                    op=op,
                    op_ctor=""
                    if info is not None and info.has_derivatives
                    else f'"{cpp.name(f.func)}"',
                    args_with_derivatives=args,
                    irange=f"{list_like_arg}.size()",
                ).split("\n")
            )
        setup.extend(emit_save_inputs())

        body.extend(
            emit_check_no_requires_grad(differentiable_inputs, args_with_derivatives)
        )
        declare_grad_fn_template = (
            DECLARE_GRAD_FN if not is_inplace_foreach else DECLARE_VECTOR_OF_GRAD_FN
        )
        body.append(declare_grad_fn_template.substitute(op=op))
        body.append(SETUP_DERIVATIVE.substitute(setup=setup))
        return body
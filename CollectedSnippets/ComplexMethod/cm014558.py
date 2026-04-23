def gen_composite_out_kernel(g: NativeFunctionsGroup) -> str | None:
    # We should only be generating these for code-generated NativeFunctions
    if "generated" not in g.out.tags:
        return None
    # And we always write the kernel for the out= op in terms of the functional.
    # Note that the functional op might have also been generated, but we don't have to
    # worry about cycles, because the generated functional kernels are always implemented
    # in terms of non-generated kernels (see gen_composite_functional_kernel).

    sig = DispatcherSignature(g.out.func)
    target_sig = DispatcherSignature(g.functional.func)

    exprs = ", ".join(
        [e.expr for e in translate(sig.arguments(), target_sig.arguments())]
    )

    copy_outs = []
    out_name = "tmp_output"
    for i, out_arg in enumerate(g.out.func.arguments.out):
        functional_return_name = (
            out_name
            if len(g.functional.func.returns) == 1
            else f"std::get<{i}>({out_name})"
        )
        copy_outs.append(
            f"""\
  resize_out_helper({out_arg.name}, {functional_return_name});
  copy_arg({out_arg.name}, {functional_return_name});"""
        )

    rets = []
    # For each return arg in the calling (out=) operator,
    # If it corresponds to an aliased input, return the input.
    # Otherwise, return the corresponding output from calling the functional operator.
    for i, ret_name in enumerate(g.out.func.aliased_return_names()):
        if ret_name is not None:
            rets.append(ret_name)
        else:
            functional_return_name = (
                out_name
                if len(g.functional.func.returns) == 1
                else f"std::get<{i}>({out_name})"
            )
            rets.append(functional_return_name)

    copy_outs_str = "\n".join(copy_outs)

    # Kernel name needs to follow the naming convention defined in `generate_function()`
    return f"""
{sig.defn(name=g.out.func.name.unambiguous_name() + ("_symint" if g.out.func.has_symint() else ""))} {{
  auto {out_name} = at::_ops::{g.functional.func.name.unambiguous_name()}::call({exprs});
  {copy_outs_str}
  {return_str(g.out.func.returns, rets)}
}}
"""
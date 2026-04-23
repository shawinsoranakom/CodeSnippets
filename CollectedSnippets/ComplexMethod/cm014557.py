def gen_composite_functional_kernel(g: NativeFunctionsGroup) -> str | None:
    # We should only be generating these for code-generated NativeFunctions
    if "generated" not in g.functional.tags:
        return None
    # And we always write the kernel for a generated op in terms of a non-generated op.
    if g.inplace is not None and "generated" not in g.inplace.tags:
        target_f = g.inplace
    elif g.mutable is not None and "generated" not in g.mutable.tags:
        target_f = g.mutable
    else:
        # We should be guaranteed to have a valid inplace/mutable variant to call into.
        # See Note: [Mutable Ops Not Using Functionalization]
        raise AssertionError(str(g.functional.func))

    sig = DispatcherSignature(g.functional.func)
    target_sig = DispatcherSignature(target_f.func)

    context: list[Binding | Expr] = []
    clone_mutable_inputs = []
    cloned_return_names = []
    # We can't just directly pass all of the arguments from the functional op into the mutating op.
    # We need to check for which inputs to the mutating operator are mutable,
    # and clone those inputs first.
    for a_curr, a_tgt in zip(
        dispatcher.jit_arguments(g.functional.func),
        dispatcher.jit_arguments(target_f.func),
    ):
        if a_tgt.annotation is not None and a_tgt.annotation.is_write:
            clone_mutable_inputs.append(
                f"auto {a_curr.name}_clone = clone_arg({a_curr.name});"
            )
            context.append(
                Expr(
                    expr=f"{a_curr.name}_clone",
                    type=dispatcher.argument_type(a_curr, binds=a_curr.name),
                )
            )
            # Invariant: mutable arguments on the inner mutable op are always returns on the functional op.
            cloned_return_names.append(f"{a_curr.name}_clone")
        else:
            context.append(dispatcher.argument(a_curr))
    exprs = ", ".join([e.expr for e in translate(context, target_sig.arguments())])

    out_name = "output"
    maybe_assign = f"auto {out_name} = " if len(target_f.func.returns) > 0 else ""
    inner_return_names = gather_nonaliased_inner_rets(target_f.func, out_name)
    ret_str = return_str(
        g.functional.func.returns, inner_return_names + cloned_return_names
    )

    clone_mutable_inputs_str = "\n".join(clone_mutable_inputs)
    return f"""
{sig.defn(name=sig.name() + ("_symint" if g.out.func.has_symint() else ""))} {{
  {clone_mutable_inputs_str}
  {maybe_assign}at::_ops::{target_f.func.name.unambiguous_name()}::call({exprs});
  {ret_str}
}}
"""
def _is_functional_graph(fx_g: torch.fx.Graph) -> tuple[str | None, int]:
    allowed_mutation_ops = [
        torch.ops.aten.copy_.default,
        torch.ops.aten.set_.source_Tensor,
    ]
    if hasattr(torch.ops.fsdp, "copy_"):
        allowed_mutation_ops.append(torch.ops.fsdp.copy_.default)

    placeholders = set()
    mutation_count = 0
    # NB: It would also be nice to verify that the mutations all happen at the
    # end, but we also do some administrative views after mutations so this
    # isn't actually true.  (TODO: Could this cause problems for Inductor?)
    error = None
    for n in fx_g.nodes:
        if n.op == "placeholder":
            placeholders.add(n)
        if isinstance(n.target, torch._ops.OpOverload):
            if n.target in allowed_mutation_ops:
                # Can only copy_/set_ into an input
                # this is mostly a hack to avoid failing XLA tests.
                # See https://github.com/pytorch/pytorch/pull/122434#issuecomment-2101012113
                if "set_buffer_donor_" not in str(n.args[0]):
                    if n.args[0] not in placeholders:
                        error = f"n={str(n)}, n.args[0]={str(n.args[0])}, placeholders={str(placeholders)}, graph={str(fx_g)}"
                mutation_count += 1
            else:
                if n.target._schema.is_mutable:
                    error = f"aot_autograd expected to have an entirely functional graph, but found {n.format_node()}"
    return error, mutation_count
def ts_compile(fx_g: fx.GraphModule, inps: Sequence[Any]) -> torch.jit.ScriptModule:
    """
    Compiles the :attr:`fx_g` with Torchscript compiler.

    .. warning::
        This API is experimental and likely to change.

    Args:
        fx_g(fx.GraphModule): The input Fx graph module to be compiled.

    Returns:
        Torch scripted model.
    """

    with _disable_jit_autocast():
        strip_overloads(fx_g)

        for node in fx_g.graph.find_nodes(
            op="call_function", target=torch.ops.aten._to_copy
        ):
            if len(node.args) == 1 and len(node.kwargs) == 1 and "dtype" in node.kwargs:
                node.target = torch.ops.aten.to

        for node in fx_g.graph.nodes:
            new_kwargs = {}
            for k, v in node.kwargs.items():
                if isinstance(v, torch.device):
                    v = v.type
                new_kwargs[k] = v
            node.kwargs = new_kwargs

        fx_g.graph.lint()

        fx_g.recompile()

        f = torch.jit.script(fx_g)

        # pyrefly: ignore [missing-attribute]
        torch._C._jit_pass_remove_mutation(f.graph)

        f = torch.jit.freeze(f.eval())
        f = torch.jit.optimize_for_inference(f)
        if not any(isinstance(t, torch._subclasses.FakeTensor) for t in inps):
            f(*inps)
    return f
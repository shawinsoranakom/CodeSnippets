def test_shape_boundary_standalone_compile():
    """
    Repro for the original production bug:

        AssertionError: out_spec mismatch
        TreeSpec(tuple, None, [*, *, TreeSpec(Size, None, [*, *]), *])
        vs
        TreeSpec(tuple, None, [*, *, *, *])

    A subgraph outputs torch.Size (e.g. torch.Size([s72, 2048])) as one of
    its values when shape info crosses a split boundary. aot_autograd / inductor
    expect all submodule outputs to be flat tensors or scalars, not torch.Size.

    With the fix, x.size() is decomposed into individual sym_size.int calls
    so only scalar SymInts cross the boundary — not the torch.Size.
    """
    from torch._inductor import standalone_compile

    captured_graph = None

    def capturing_backend(gm: fx.GraphModule, example_inputs: list) -> fx.GraphModule:
        nonlocal captured_graph
        captured_graph = gm
        return gm

    def model_fn(x: torch.Tensor) -> torch.Tensor:
        shape = x.size()
        x = torch.ops.aten.sigmoid.default(x)
        x = x.clone().view(shape)
        return x

    x = torch.randn(4, 8)
    torch._dynamo.mark_dynamic(x, 0)
    torch.compile(model_fn, backend=capturing_backend)(x)

    split_gm, split_items = split_graph(captured_graph, ["aten::sigmoid"])
    assert len(split_items) == 3

    # Verify that the consumer subgraph only has a placeholder for the dynamic
    # dim (SymInt) — the static dim (8) should be inlined as a literal, not
    # threaded as a placeholder.
    consumer = split_items[-1]  # valid since len == 3: [producer, sigmoid, consumer]
    symint_placeholders = [
        n
        for n in consumer.graph.graph.nodes
        if n.op == "placeholder"
        and isinstance(n.meta.get("example_value"), torch.SymInt)
    ]
    static_int_placeholders = [
        n
        for n in consumer.graph.graph.nodes
        if n.op == "placeholder"
        and isinstance(n.meta.get("example_value"), int)
        and not isinstance(n.meta.get("example_value"), torch.SymInt)
    ]
    assert len(symint_placeholders) >= 1, (
        "Consumer should have a SymInt placeholder for the dynamic dim."
    )
    assert len(static_int_placeholders) == 0, (
        "Static dims should be inlined as literals, not threaded as placeholders."
    )

    submod_0 = split_gm.submod_0

    standalone_compile(
        submod_0, [torch.randn(4, 8), 4], dynamic_shapes="from_example_inputs"
    )
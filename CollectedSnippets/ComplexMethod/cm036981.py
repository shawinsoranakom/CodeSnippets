def test_symint_crosses_split_boundary():
    """
    Test that SymInt placeholders from torch.compile + mark_dynamic
    cross split boundaries safely via split_module's natural threading.

    SymInt values are threaded through subgraphs by split_module and
    handled correctly by inductor — no special replacement is needed.
    """
    captured_graph = None

    def capturing_backend(gm: fx.GraphModule, example_inputs: list) -> fx.GraphModule:
        nonlocal captured_graph
        captured_graph = gm
        return gm

    def model_fn(x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        hidden_size = x.shape[1]
        x = torch.ops.aten.sigmoid.default(x)
        x = x.clone().view(batch_size, hidden_size)
        x = torch.ops.aten.sigmoid.default(x)
        x = x.clone().view(batch_size, hidden_size)
        x = torch.ops.aten.sigmoid.default(x)
        x = x.clone().view(batch_size, hidden_size)
        return x

    x = torch.randn(4, 8)
    torch._dynamo.mark_dynamic(x, 0)

    compiled_fn = torch.compile(model_fn, backend=capturing_backend)
    compiled_fn(x)

    assert captured_graph is not None, "Graph should be captured by backend"

    # SymInt placeholders should exist in the captured graph
    symint_placeholders = [
        node
        for node in captured_graph.graph.nodes
        if node.op == "placeholder"
        and isinstance(node.meta.get("example_value"), torch.SymInt)
    ]
    assert len(symint_placeholders) > 0, (
        "Captured graph should have SymInt placeholders from mark_dynamic."
    )

    # split_graph should handle SymInt placeholders without error
    split_gm, split_items = split_graph(captured_graph, ["aten::sigmoid"])

    # Should have 3 splitting subgraphs (3 sigmoids)
    splitting_subgraphs = [item for item in split_items if item.is_splitting_graph]
    assert len(splitting_subgraphs) == 3, (
        f"Expected 3 splitting subgraphs (3 sigmoids), got {len(splitting_subgraphs)}"
    )
    assert len(split_items) >= 6, (
        f"Expected at least 6 total subgraphs, got {len(split_items)}"
    )
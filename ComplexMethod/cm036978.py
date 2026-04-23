def test_getitem_moved_to_producer_subgraph():
    """
    Test that getitem operations are moved to the same subgraph as their input,
    preventing tuple inputs to submodules.
    """

    def model_fn(x: torch.Tensor) -> torch.Tensor:
        # torch.split returns a tuple, creating real getitem operations
        # Should become first submodule that produces tuple
        chunks = torch.split(x, x.shape[0] // 2, dim=0)

        # Following ops should become second submodule that consumes tuple
        result_0 = torch.relu(chunks[0])
        result_1 = torch.relu(chunks[1])
        return torch.cat([result_0, result_1], dim=0)

    x = torch.randn(4, 3)
    gm = make_fx(model_fn)(x)

    has_getitem = any(
        node.op == "call_function" and node.target == operator.getitem
        for node in gm.graph.nodes
    )
    assert has_getitem, "Test setup failed: graph should contain getitem operations"

    # Split on tuple producer aten::split
    split_ops = ["aten::split.Tensor"]
    split_gm, split_items = split_graph(gm, split_ops)
    assert len(split_items) == 2, "Graph should be split into 2 submodules"

    for split_item in split_items:
        submodule = split_item.graph

        getitem_on_placeholder = []
        for node in submodule.graph.nodes:
            if (
                node.op == "call_function"
                and node.target == operator.getitem
                and node.args[0].op == "placeholder"
            ):
                getitem_on_placeholder.append(node)

        assert len(getitem_on_placeholder) == 0, (
            f"Submodule {split_item.submod_name} has getitem operations on "
            f"placeholder nodes: {[n.name for n in getitem_on_placeholder]}. "
            "This means tuple inputs were not properly eliminated."
        )

    new_x = torch.randn(4, 3)
    output_original = gm(new_x)
    output_split = split_gm(new_x)

    assert torch.allclose(output_original, output_split), "Output mismatch"
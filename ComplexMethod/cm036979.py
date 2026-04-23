def test_no_tuple_inputs_with_multiple_consumers():
    """
    Test that when a tuple is consumed by multiple split operations,
    getitem operations are properly moved to avoid tuple inputs.
    """

    def model_fn(x: torch.Tensor) -> torch.Tensor:
        # torch.split returns a tuple, creating real getitem operations
        # Should become first submodule that produces tuple
        chunks = torch.split(x, x.shape[0] // 2, dim=0)

        # These should become second submodule consuming tuple
        result_1 = torch.relu(chunks[0])
        result_2 = torch.relu(chunks[1])

        # Artificial graph splitting point to create another
        # independent submodule that consumes tuple later
        # This would become the third submodule
        result_1 = torch.sigmoid(result_1)

        # Fourth submodule that consumes tuple
        result = torch.cat([chunks[0], chunks[1], result_1, result_2])
        return result

    x = torch.randn(4, 3)
    gm = make_fx(model_fn)(x)

    has_getitem = any(
        node.op == "call_function" and node.target == operator.getitem
        for node in gm.graph.nodes
    )
    assert has_getitem, "Test setup failed: graph should contain getitem operations"

    split_ops = ["aten::split.Tensor", "aten::sigmoid"]
    split_gm, split_items = split_graph(gm, split_ops)
    assert len(split_items) == 4, "Graph should be split into 4 submodules"

    for split_item in split_items:
        submodule = split_item.graph

        for node in submodule.graph.nodes:
            if (
                node.op == "call_function"
                and node.target == operator.getitem
                and node.args[0].op == "placeholder"
            ):
                pytest.fail(
                    f"Submodule {split_item.submod_name} has getitem on "
                    f"placeholder {node.args[0].name}, indicating it receives "
                    "a tuple input"
                )

    new_x = torch.randn(4, 3)
    output_original = gm(new_x)
    output_split = split_gm(new_x)

    assert torch.allclose(output_original, output_split), "Output mismatch after split"
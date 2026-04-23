def test_consecutive_ops_in_split():
    """
    Test that consecutive splitting operations are grouped into the same subgraph
    """

    def model_fn(x: torch.Tensor) -> torch.Tensor:
        """
        Define a simple model where consecutive operations create opportunities
        for splitting subgraphs.
        """
        # Apply silly attention followed by consecutive operations
        intermediate = torch.relu(x)
        attn_inout = torch.sqrt(intermediate)
        torch.ops.silly.attention(intermediate, intermediate, attn_inout, attn_inout)
        final_result = torch.sigmoid(attn_inout)
        return final_result

    torch.set_default_device(DEVICE_TYPE)

    # Create the traced FX graph for the model
    x = torch.randn(8, 4)

    gm = make_fx(model_fn)(x)

    # Assert presence of the expected operations in the setup
    assert (
        len(list(find_op_nodes(torch.ops.aten.relu, gm.graph))) == 1
        and len(list(find_op_nodes(torch.ops.aten.sqrt, gm.graph))) == 1
    ), "Test setup failed: Expected sqrt and relu operations in the graph."

    # Configure split operations to test
    splitting_ops = ["silly::attention", "aten::sqrt"]
    split_gm, split_items = split_graph(gm, splitting_ops)

    # Validate the number of partitions
    assert len(split_items) == 3, (
        "Consecutive splitting operations were not grouped correctly."
    )

    # Validate that correctness is preserved
    new_x = torch.randn(8, 4)
    output_original = gm(new_x)
    output_split = split_gm(new_x)
    assert torch.allclose(output_original, output_split), (
        "Output mismatch after splitting."
    )

    # Check the splitting item has 2 nodes exactly (relu and attn)
    splitting_items = list(s for s in split_items if s.is_splitting_graph)
    assert len(splitting_items) == 1, "Expecting a single splitting graph"
    print(splitting_items[0].graph.graph)
    splitting_gm = splitting_items[0].graph
    assert len(splitting_gm.graph.nodes) == 4, "Expecting 4 nodes in splitting graph"
    assert [node.op for node in splitting_gm.graph.nodes] == ["placeholder"] + 2 * [
        "call_function"
    ] + ["output"]
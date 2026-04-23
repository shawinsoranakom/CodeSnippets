def test_size_used_in_multiple_consumer_subgraphs():
    """
    Validates that x.size() (whole shape) used by multiple downstream subgraphs
    does not cause torch.Size to cross split boundaries.

    Model:
        shape = x.size()          # whole shape — must not cross as torch.Size
        z1 = sigmoid(x)           # split point 1
        y1 = y.view(shape)        # consumer 1 uses shape
        z2 = sigmoid(z1)          # split point 2
        y2 = y.view(shape)        # consumer 2 uses shape again

    Without the fix, torch.Size crosses the boundary as a submodule output,
    which aot_autograd / standalone_compile rejects.
    """
    captured_graph = None
    captured_inputs = None

    def capturing_backend(gm: fx.GraphModule, example_inputs: list) -> fx.GraphModule:
        nonlocal captured_graph, captured_inputs
        captured_graph = gm
        captured_inputs = example_inputs
        return gm

    def model_fn(x: torch.Tensor, y: torch.Tensor) -> torch.Tensor:
        shape = x.size()
        z1 = torch.ops.aten.sigmoid.default(x)
        y1 = y.view(shape)
        z2 = torch.ops.aten.sigmoid.default(z1)
        y2 = y.view(shape)
        return z2 + y1 + y2

    x = torch.randn(4, 8)
    y = torch.randn(4, 8)  # same shape as x so view(shape) doesn't specialize dim 0
    torch._dynamo.mark_dynamic(x, 0)
    torch._dynamo.mark_dynamic(y, 0)
    torch.compile(model_fn, backend=capturing_backend)(x, y)

    split_gm, split_items = split_graph(captured_graph, ["aten::sigmoid"])

    splitting_items = [item for item in split_items if item.is_splitting_graph]
    assert len(splitting_items) == 2

    # Verify functional correctness — fails without the fix because torch.Size
    # would cross a split boundary as a submodule output
    output_original = model_fn(x, y)
    output_split = split_gm(*captured_inputs)
    if isinstance(output_split, tuple):
        output_split = next(o for o in output_split if isinstance(o, torch.Tensor))
    assert torch.allclose(output_original, output_split), "Output mismatch after split"
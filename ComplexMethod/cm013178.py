def _assert_module_states(
    model: nn.Module,
    process_group: dist.ProcessGroup,
    assert_fn: Callable,
):
    """
    All-gathers module states across ranks and calls ``assert_fn`` on each pair
    of corresponding states from rank 0 and a nonzero rank. For example, if
    ``assert_fn`` is ``self.assertEqual()``, then this checks that all module
    states are equal across ranks.
    """
    # Include names for debugging convenience
    named_module_states = [
        (param_name, param.detach().cpu())
        for param_name, param in model.named_parameters()
    ]
    named_module_states += [
        (buffer_name, buffer.detach().cpu())
        for buffer_name, buffer in model.named_buffers()
    ]
    world_size = dist.get_world_size(process_group)
    olist = [None for _ in range(world_size)]
    dist.all_gather_object(olist, named_module_states, group=process_group)
    rank0_states = olist[0]
    if rank0_states is None:
        raise AssertionError("Expected rank0_states to not be None")  # mypy
    for state in olist[1:]:
        if state is None:
            raise AssertionError("Expected state to not be None")  # mypy
        for (_, p1), (_, p2) in zip(rank0_states, state, strict=True):
            assert_fn(p1, p2)
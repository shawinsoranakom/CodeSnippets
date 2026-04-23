def validate_combination(
    op: Callable[..., Any],
    sample_input: SampleInput,
    tensors: list[tuple[str, torch.Tensor]],
    combination: PlacementCombination,
    ground_truth: torch.Tensor | list[torch.Tensor],
    world_size: int = 2,
    mesh: DeviceMesh | None = None,
    mask_shift: int = 0,
) -> tuple[bool | None, str]:
    """
    Validate a single placement combination against ground truth.

    Returns (True, "") if valid, (False, error_msg) if invalid, or
    (None, reason) if the combination cannot be tested (e.g. uneven shards).

    The validation logic:
    1. Shard inputs according to input placements to get local tensors
    2. Run the raw op on local tensors (bypassing DTensor dispatch)
    3. Wrap the local output in a DTensor with the claimed output placement
    4. Redistribute to Replicate and compare with ground truth

    Args:
        op: The operator function
        sample_input: The SampleInput with original arguments
        tensors: List of (name, tensor) pairs extracted from sample
        combination: The placement combination to validate
        ground_truth: Expected output tensor(s). For multi-output ops, a list
            of tensors where each element is validated independently against
            the same output placement.
        world_size: Number of simulated ranks
        mesh: Optional pre-created device mesh (for performance)

    Returns:
        (is_valid, error_message)
    """
    try:
        if mesh is None:
            device = tensors[0][1].device.type if tensors else "cpu"
            mesh = init_device_mesh(device, (world_size,))

        # Uneven shards produce SymInt in LocalTensor's wrapper shape,
        # which breaks C++ overload resolution before __torch_dispatch__
        # can intercept. Return None to signal "untestable".
        for (name, tensor), placement in zip(tensors, combination[0]):
            if isinstance(placement, Shard):
                if tensor.size(placement.dim) % world_size != 0:
                    return None, "uneven shard"

        local_tensors = _shard_tensors(
            tensors, combination[0], world_size, mesh, mask_shift
        )

        local_idx = 0

        def _replace_with_local(a):
            nonlocal local_idx
            if isinstance(a, torch.Tensor):
                local = local_tensors[local_idx]
                local_idx += 1
                return local
            return a

        if isinstance(sample_input.input, torch.Tensor):
            local_input = _replace_with_local(sample_input.input)
        else:
            local_input = pytree.tree_map(_replace_with_local, sample_input.input)

        local_args = pytree.tree_map(_replace_with_local, sample_input.args)
        local_kwargs = pytree.tree_map(_replace_with_local, sample_input.kwargs)

        local_output = op(local_input, *local_args, **local_kwargs)

        return _compare_outputs(
            local_output, ground_truth, combination[1], mesh, world_size
        )

    except Exception as e:
        # TODO: This is too broad. Consider: (1) explicit checks for shard dim
        # validity and shape compatibility before calling tensor_split/from_local,
        # (2) scoped try/except around op() and redistribute() that raise specific
        # exceptions (e.g., UnsupportedRedistribute, OpError), and (3) only
        # catching those here, letting real bugs propagate.
        return False, f"Exception: {type(e).__name__}: {e}"
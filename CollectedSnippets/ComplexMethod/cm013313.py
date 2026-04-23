def validate_sharding_rule_sample(
    op, full_args, full_kwargs, input_placements, output_placements, device_mesh
):
    from torch.utils import _pytree as pytree

    # Extract tensors from args in order, pair with placements
    full_tensors = [
        a for a in pytree.tree_leaves(full_args) if isinstance(a, torch.Tensor)
    ]
    full_tensors += [
        a for a in pytree.tree_leaves(full_kwargs) if isinstance(a, torch.Tensor)
    ]

    dtensors = [
        distribute_tensor(t, device_mesh, (p,))
        for t, p in zip(full_tensors, input_placements)
    ]

    # Build sharded args by replacing tensors with their sharded local versions
    dtensor_idx = 0

    def _to_local_shard(a):
        nonlocal dtensor_idx
        if isinstance(a, torch.Tensor):
            local = dtensors[dtensor_idx].to_local()
            dtensor_idx += 1
            return local
        return a

    local_args, local_kwargs = pytree.tree_map(
        _to_local_shard, (full_args, full_kwargs)
    )

    # run and compare
    ref_output = op(*full_args, **full_kwargs)
    local_output = op(*local_args, **local_kwargs)

    ref_tensors = [
        t for t in pytree.tree_leaves(ref_output) if isinstance(t, torch.Tensor)
    ]
    local_tensors = [
        t for t in pytree.tree_leaves(local_output) if isinstance(t, torch.Tensor)
    ]

    for ref, local, plc in zip(ref_tensors, local_tensors, output_placements):
        dt = DTensor.from_local(local, device_mesh, (plc,))
        full = dt.redistribute(device_mesh, (Replicate(),)).to_local()
        if ref.shape != full.shape or not torch.allclose(
            ref, full, atol=1e-5, rtol=1e-5, equal_nan=True
        ):
            return False
    return True
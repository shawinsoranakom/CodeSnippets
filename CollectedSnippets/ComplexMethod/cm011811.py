def check_and_broadcast_indices(indices, device):
    assert all(
        i.get_dtype() in (torch.int64, torch.int32, torch.bool, torch.uint8)
        for i in indices
        if i is not None
    ), (
        f"indices must be int64, byte or bool. Got {[i.get_dtype() for i in indices if i is not None]}"
    )
    if any(
        i.get_dtype() in (torch.bool, torch.uint8) for i in indices if i is not None
    ):
        raise NotImplementedError("Fallback for bool indices")

    valid_idxs = [i for i, x in enumerate(indices) if isinstance(x, TensorBox)]
    assert len(valid_idxs) > 0, "requires at least 1 non-None index"
    new_indices = [None] * len(indices)
    for i, x in zip(valid_idxs, broadcast_tensors(*[indices[i] for i in valid_idxs])):
        # Eager allows indices to be CPU tensor when running on CUDA
        # FIXME: Calling to_device(x, device) should work but
        # test_advancedindex_mixed_cpu_devices still fails
        if x.get_device() != device:
            raise NotImplementedError("Fallback when indices is on a different device")
        new_indices[i] = x
    return new_indices, valid_idxs
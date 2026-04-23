def collect_fw_donated_buffer_idxs(
    fw_ins: list[FakeTensor | None],
    user_fw_outs: list[FakeTensor | None],
    bw_outs: list[FakeTensor | None],
    saved_tensors: list[FakeTensor | None],
) -> list[int]:
    """
    Checks if the saved tensors are donated buffers, which means a saved tensor is not
    an alias of any tensors in fw_ins, user_fw_outs, and bw_outs.
    """

    storage_refs = set()

    for t in itertools.chain(fw_ins, user_fw_outs, bw_outs):
        # Only access storage if a tensor has storage (not sparse)
        if t is not None and isinstance(t, FakeTensor) and not is_sparse_any(t):
            storage_refs.add(StorageWeakRef(t.untyped_storage()))

    num_saved_tensor = len(saved_tensors)
    donated_buffer_idxs = []
    for i in range(num_saved_tensor):
        t = saved_tensors[i]
        if (
            t is not None
            and isinstance(t, FakeTensor)
            and not is_sparse_any(t)
            and StorageWeakRef(t.untyped_storage()) not in storage_refs
        ):
            donated_buffer_idxs.append(i)

    return donated_buffer_idxs
def check_memory_pool(
    device: int,
    pool_id: tuple[int, int],
    live_storages_ptrs: list[StorageWeakRefWrapper],
) -> None:
    """Validate cudagraph pool allocations against tracked live storages and surface leaks."""
    assert all(isinstance(elem, StorageWeakRefWrapper) for elem in live_storages_ptrs)
    unique_storages = {stor.data_ptr() for stor in live_storages_ptrs if stor()}  # noqa: set_linter

    # check if there is a divergence first, then do the expensive snapshot call after
    # we know it will error
    if torch._C._cuda_checkPoolLiveAllocations(device, pool_id, unique_storages):
        return

    # at this point we are past the fast-path. we have seen rare cases where a dead tensor is dead,
    # but hasn't been gc'd yet, and gives false positive for allocated_not_in_live_storages
    gc.collect()
    torch.cuda.synchronize()

    segments = get_cudagraph_segments(pool_id)

    allocated_not_in_live_storages = {}

    for segment in segments:
        addr = segment["address"]
        for block in segment["blocks"]:
            if block["state"] == "active_allocated":
                if addr not in unique_storages:
                    allocated_not_in_live_storages[addr] = block
                else:
                    unique_storages.remove(addr)

            addr += block["size"]

    torch._check(
        len(unique_storages) == 0,
        lambda: (
            f"These storage data ptrs are not allocated in pool {pool_id} but should be: {unique_storages}. "
            f"This could be a bug in inductor aliasing tracking or in a custom op's meta function. Please file an issue."
        ),
    )

    if len(allocated_not_in_live_storages) != 0:
        formatted = []
        for dp, block in allocated_not_in_live_storages.items():
            trace = format_tb(block.get("frames", []))
            # pyrefly: ignore [bad-argument-type]
            formatted.append(f"Data Pointer: {dp}, history: \n{trace}")
        formatted_s = "\n".join(formatted)

        history_hint = ""
        if not config.triton.cudagraph_trees_history_recording:
            history_hint = "- Set torch._inductor.config.triton.cudagraph_trees_history_recording = True for allocation origins\n"

        objgraph_hint = (
            (
                "- Objgraph backrefs disabled; set torch._inductor.config.triton.cudagraph_trees_objgraph = True "
                "(refs_live_tensor_{index}.svg)\n"
            )
            if not config.triton.cudagraph_trees_objgraph
            else ""
        )
        objgraph_files_hint = ""

        if config.triton.cudagraph_trees_objgraph:
            # pyrefly: ignore  # import-error
            import objgraph

            generated_files: list[str] = []

            tensors = objgraph.by_type("torch.Tensor")
            for index, bad_dp in enumerate(allocated_not_in_live_storages):
                bad_tensor = next(
                    (t for t in tensors if bad_dp in collect_cuda_data_ptrs(t)), None
                )
                if bad_tensor is None:
                    continue
                filename = f"refs_live_tensor_{index}.svg"
                objgraph.show_backrefs(bad_tensor, filename=filename, max_depth=5)
                generated_files.append(filename)
            if generated_files:
                objgraph_files_hint = (
                    f"- Objgraph backrefs written: {', '.join(generated_files)}\n"
                )

        dangling_addrs = OrderedSet(allocated_not_in_live_storages.keys())
        msg = (
            f"Detected {len(allocated_not_in_live_storages)} tensor(s) in the cudagraph pool not tracked as outputs. "
            f"All live allocations must be tracked for correctness.\n"
            f"Debugging:\n"
            f"{history_hint}"
            f"{objgraph_hint}"
            f"- Search gc.get_objects() for tensors with data_ptr() in {dangling_addrs}\n"
            f"- Use refcycle to find what is preventing cleanup\n"
            f"{objgraph_files_hint}"
            f"Allocations:\n{formatted_s}"
        )
        raise RuntimeError(msg)
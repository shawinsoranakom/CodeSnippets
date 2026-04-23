def qr_variable_input(rank, world_size):
    """
    When the tensor parallelism is set to 4 or 8, frequent changes
    in the input shape can cause QuickReduce to hang (this issue
    has been observed with the gpt_oss model).
    """
    device = torch.device(f"cuda:{rank}")
    torch.accelerator.set_device_index(device)
    qr_max_size = None  # MB
    _ptr = ops.init_custom_qr(rank, world_size, qr_max_size)
    ranks = []
    for i in range(world_size):
        ranks.append(i)
    dist.init_process_group(
        backend="nccl",
        init_method="tcp://127.0.0.1:29500",
        rank=rank,
        world_size=world_size,
    )
    cpu_group = torch.distributed.new_group(ranks, backend="nccl")

    handle = ops.qr_get_handle(_ptr)
    world_size = dist.get_world_size(group=cpu_group)
    handles = [None] * world_size
    dist.all_gather_object(handles, handle, group=cpu_group)
    ops.qr_open_handles(_ptr, handles)

    num = 1
    s1 = 1024
    while num < 50000:  # 50000 is sufficient to identify issues.
        dtype = torch.float16
        device_idx = torch.accelerator.current_device_index()
        if num % 2 == 0:
            s2 = 1024
            inp1 = torch.zeros((s1, s2), dtype=dtype, device=device_idx)
        else:
            s2 = 2048
            inp1 = torch.ones((s1, s2), dtype=dtype, device=device_idx)
        result = torch.empty_like(inp1)
        # FP = 0 INT8 = 1 INT6 = 2 INT4 = 3 NONE = 4
        ops.qr_all_reduce(_ptr, inp1, result, 3, cast_bf2half=True)
        try:
            if inp1[0, 0] == 0:
                assert torch.all(result == 0)
            else:
                assert torch.all(result == world_size)
        except AssertionError:
            print("Assertion failed! Allreduce results are incorrect.")
            raise
        num += 1
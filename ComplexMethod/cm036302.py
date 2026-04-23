def test_transfer(
    default_vllm_config,
    gpu_to_cpu: bool,
    num_mappings: int,
    gpu_page_size_bytes: int,
    block_size_factor: int,
    num_gpu_blocks: int,
    num_cpu_blocks: int,
    num_tensors: int,
    seed: int,
    device: str,
    use_shared_memory: bool,
) -> None:
    set_random_seed(seed)

    # build CanonicalKVCacheTensor list: one per tensor
    kv_cache_tensors: list[CanonicalKVCacheTensor] = []
    for i in range(num_tensors):
        gpu_tensor = torch.zeros(
            (num_gpu_blocks, gpu_page_size_bytes),
            dtype=torch.int8,
            device=device,
        )
        kv_cache_tensors.append(
            CanonicalKVCacheTensor(
                tensor=gpu_tensor,
                page_size_bytes=gpu_page_size_bytes,
            )
        )

    # one group containing all tensors, one data ref per tensor
    kv_cache_groups_data_refs: list[list[CanonicalKVCacheRef]] = [
        [
            CanonicalKVCacheRef(
                tensor_idx=i,
                page_size_bytes=gpu_page_size_bytes,
            )
            for i in range(num_tensors)
        ]
    ]

    kv_caches = CanonicalKVCaches(
        tensors=kv_cache_tensors,
        group_data_refs=kv_cache_groups_data_refs,
    )

    mmap_region: SharedOffloadRegion | None = None
    if use_shared_memory:
        cpu_page_size = gpu_page_size_bytes * num_tensors * block_size_factor
        mmap_region = SharedOffloadRegion(
            instance_id=str(uuid.uuid4()),
            total_size_bytes=num_cpu_blocks * cpu_page_size,
            num_blocks=num_cpu_blocks,
            rank=0,
            num_workers=1,
            cpu_page_size=cpu_page_size,
        )

    handlers = CpuGpuOffloadingHandlers(
        kv_caches=kv_caches,
        block_size_factor=block_size_factor,
        num_cpu_blocks=num_cpu_blocks,
        mmap_region=mmap_region,
    )

    # select block mappings
    gpu_blocks = random.sample(range(num_gpu_blocks), num_mappings * block_size_factor)
    cpu_blocks = random.sample(range(num_cpu_blocks), num_mappings)

    # expand cpu blocks to gpu-page granularity for uniform comparison:
    # each cpu block maps to block_size_factor consecutive sub-blocks
    cpu_blocks_expanded = [
        cpu_block * block_size_factor + j
        for cpu_block in cpu_blocks
        for j in range(block_size_factor)
    ]

    # maybe skip some GPU blocks to test reading/writing from the middle of a CPU block
    blocks_to_skip = block_size_factor - 1
    if blocks_to_skip > 0:
        gpu_blocks = gpu_blocks[blocks_to_skip:]
        cpu_blocks_expanded = cpu_blocks_expanded[blocks_to_skip:]

    # set transfer direction
    if gpu_to_cpu:
        handler = handlers.gpu_to_cpu_handler
        src_spec = GPULoadStoreSpec(
            gpu_blocks, group_sizes=(len(gpu_blocks),), block_indices=(blocks_to_skip,)
        )
        dst_spec = CPULoadStoreSpec(cpu_blocks)
        dst_to_src = dict(zip(cpu_blocks_expanded, gpu_blocks))
        num_dst_sub_blocks = num_gpu_blocks
    else:
        handler = handlers.cpu_to_gpu_handler
        src_spec = CPULoadStoreSpec(cpu_blocks)
        dst_spec = GPULoadStoreSpec(
            gpu_blocks, group_sizes=(len(gpu_blocks),), block_indices=(blocks_to_skip,)
        )
        dst_to_src = dict(zip(gpu_blocks, cpu_blocks_expanded))
        num_dst_sub_blocks = num_gpu_blocks

    # randomize src and dst tensors before transfer
    for tensor in handler.src_tensors:
        tensor.random_()
    for tensor in handler.dst_tensors:
        tensor.random_()

    # clone src and dst tensors before transfer
    orig_src_tensors = [x.clone() for x in handler.src_tensors]
    orig_dst_tensors = [x.clone() for x in handler.dst_tensors]

    # call transfer function
    start_time = time.time()
    assert handler.transfer_async(1, (src_spec, dst_spec))
    assert {x.job_id for x in handler._transfers} == {1}

    # wait for transfer to complete
    end_time = time.time() + 10
    while time.time() < end_time:
        finished = handler.get_finished()
        if finished:
            assert finished[0].job_id == 1
            assert finished[0].success
            assert (
                finished[0].transfer_type == ("GPU", "CPU")
                if gpu_to_cpu
                else ("CPU", "GPU")
            )
            assert finished[0].transfer_size == (
                len(gpu_blocks)
                * sum([x.page_size_bytes for x in handler.kv_cache_groups_data_refs[0]])
            )
            assert finished[0].transfer_time > 0
            assert finished[0].transfer_time < (time.time() - start_time)
            break
        time.sleep(0.1)

    # verify src tensors did not change
    for orig_tensor, tensor in zip(orig_src_tensors, handler.src_tensors):
        assert torch.equal(orig_tensor, tensor)

    # verify dst tensors at gpu-page granularity.
    for src_tensor, dst_tensor, orig_dst_tensor in zip(
        handler.src_tensors,
        handler.dst_tensors,
        orig_dst_tensors,
    ):
        # view both GPU and CPU tensors as (n, gpu_page_size_bytes) for comparison.
        src_view = src_tensor.reshape(-1, gpu_page_size_bytes)
        dst_view = dst_tensor.reshape(-1, gpu_page_size_bytes)
        orig_dst_view = orig_dst_tensor.reshape(-1, gpu_page_size_bytes)
        for dst_sub_block in range(num_dst_sub_blocks):
            src_sub_block = dst_to_src.get(dst_sub_block)
            if src_sub_block is not None:
                expected = src_view[src_sub_block]
            else:
                expected = orig_dst_view[dst_sub_block]
            torch.testing.assert_close(dst_view[dst_sub_block].cpu(), expected.cpu())

    # Drop loop-variable refs so mmap_obj has no exported buffers at cleanup.
    del orig_tensor, tensor, src_tensor, dst_tensor, orig_dst_tensor
    del src_view, dst_view, orig_dst_view, expected

    handlers.cpu_to_gpu_handler.shutdown()
    handlers.gpu_to_cpu_handler.shutdown()
    if mmap_region:
        mmap_region.cleanup()
def test_transfer_multi_group(
    default_vllm_config,
    gpu_to_cpu: bool,
    num_mappings_per_group: int,
    gpu_page_size_bytes: int,
    block_size_factor: int,
    num_gpu_blocks: int,
    num_cpu_blocks: int,
    seed: int,
    device: str,
) -> None:
    """Test transfers with three KV cache groups:
    - Group 0: aligned transfer with num_mappings_per_group blocks
    - Group 1: zero blocks (empty group)
    - Group 2: unaligned CPU->GPU transfer (logical_offset=block_size_factor-1,
      causing the implementation to skip source sub-blocks) with
      num_mappings_per_group blocks
    """
    set_random_seed(seed)

    # 3 groups, each with 2 tensors
    num_groups = 3
    tensors_per_group = 2
    num_tensors = num_groups * tensors_per_group
    kv_cache_tensors: list[CanonicalKVCacheTensor] = []
    for _ in range(num_tensors):
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

    kv_cache_groups_data_refs: list[list[CanonicalKVCacheRef]] = [
        [
            CanonicalKVCacheRef(
                tensor_idx=g * tensors_per_group + i,
                page_size_bytes=gpu_page_size_bytes,
            )
            for i in range(tensors_per_group)
        ]
        for g in range(num_groups)
    ]

    canonical_kv_caches = CanonicalKVCaches(
        tensors=kv_cache_tensors, group_data_refs=kv_cache_groups_data_refs
    )

    handlers = CpuGpuOffloadingHandlers(
        kv_caches=canonical_kv_caches,
        block_size_factor=block_size_factor,
        num_cpu_blocks=num_cpu_blocks,
    )

    # group 0: aligned, group 1: empty, group 2: unaligned on CPU->GPU
    group_sizes_in_cpu_blocks = [num_mappings_per_group, 0, num_mappings_per_group]

    total_cpu_blocks = sum(group_sizes_in_cpu_blocks)
    total_gpu_blocks_needed = total_cpu_blocks * block_size_factor
    gpu_blocks_all = random.sample(range(num_gpu_blocks), total_gpu_blocks_needed)
    cpu_blocks_all = random.sample(range(num_cpu_blocks), total_cpu_blocks)

    # split gpu/cpu blocks per group
    gpu_blocks_per_group: list[list[int]] = []
    cpu_blocks_per_group: list[list[int]] = []
    gpu_offset = 0
    cpu_offset = 0
    for size in group_sizes_in_cpu_blocks:
        gpu_count = size * block_size_factor
        gpu_blocks_per_group.append(gpu_blocks_all[gpu_offset : gpu_offset + gpu_count])
        cpu_blocks_per_group.append(cpu_blocks_all[cpu_offset : cpu_offset + size])
        gpu_offset += gpu_count
        cpu_offset += size

    # expand cpu blocks to gpu-page granularity
    cpu_blocks_expanded_per_group = [
        [
            cpu_block * block_size_factor + j
            for cpu_block in cpu_blocks
            for j in range(block_size_factor)
        ]
        for cpu_blocks in cpu_blocks_per_group
    ]

    # skip sub-blocks from group 2 to test unaligned transfers.
    sub_blocks_to_skip = block_size_factor - 1  # e.g. 2 when block_size_factor=3
    if sub_blocks_to_skip > 0:
        gpu_blocks_per_group[2] = gpu_blocks_per_group[2][
            sub_blocks_to_skip:-sub_blocks_to_skip
        ]
        cpu_blocks_expanded_per_group[2] = cpu_blocks_expanded_per_group[2][
            sub_blocks_to_skip:-sub_blocks_to_skip
        ]

    # build flat gpu_blocks list and group_sizes in GPU blocks
    gpu_blocks: list[int] = []
    group_sizes: list[int] = []
    for gpu_blks in gpu_blocks_per_group:
        gpu_blocks.extend(gpu_blks)
        group_sizes.append(len(gpu_blks))

    # build flat cpu_blocks list
    cpu_blocks = []
    for cpu_blks in cpu_blocks_per_group:
        cpu_blocks.extend(cpu_blks)

    # block_indices: only relevant for unaligned transfers
    block_indices: list[int] = [0, 0, sub_blocks_to_skip]

    if gpu_to_cpu:
        handler = handlers.gpu_to_cpu_handler
        src_spec = GPULoadStoreSpec(
            gpu_blocks, group_sizes=group_sizes, block_indices=block_indices
        )
        dst_spec = CPULoadStoreSpec(cpu_blocks)
        # per-group mapping: cpu sub-block -> gpu sub-block
        dst_to_src_per_group = [
            dict(zip(expanded, gpu_blks))
            for expanded, gpu_blks in zip(
                cpu_blocks_expanded_per_group, gpu_blocks_per_group
            )
        ]
        num_dst_sub_blocks = num_cpu_blocks * block_size_factor
    else:
        handler = handlers.cpu_to_gpu_handler
        src_spec = CPULoadStoreSpec(cpu_blocks)
        dst_spec = GPULoadStoreSpec(
            gpu_blocks, group_sizes=group_sizes, block_indices=block_indices
        )
        # per-group mapping: gpu sub-block -> cpu sub-block
        dst_to_src_per_group = [
            dict(zip(gpu_blks, expanded))
            for gpu_blks, expanded in zip(
                gpu_blocks_per_group, cpu_blocks_expanded_per_group
            )
        ]
        num_dst_sub_blocks = num_gpu_blocks

    # randomize src and dst tensors before transfer
    for tensor in handler.src_tensors:
        tensor.random_()
    for tensor in handler.dst_tensors:
        tensor.random_()

    orig_src_tensors = [x.clone() for x in handler.src_tensors]
    orig_dst_tensors = [x.clone() for x in handler.dst_tensors]

    assert handler.transfer_async(1, (src_spec, dst_spec))
    assert {x.job_id for x in handler._transfers} == {1}

    end_time = time.time() + 10
    while time.time() < end_time:
        finished = handler.get_finished()
        if finished:
            assert finished[0].job_id == 1
            assert finished[0].success
            expected_bytes = sum(
                group_size * sum([x.page_size_bytes for x in data_refs])
                for group_size, data_refs in zip(
                    group_sizes, handler.kv_cache_groups_data_refs
                )
            )
            assert finished[0].transfer_size == expected_bytes
            break
        time.sleep(0.1)

    # verify src tensors did not change
    for orig_tensor, tensor in zip(orig_src_tensors, handler.src_tensors):
        assert torch.equal(orig_tensor, tensor)

    # verify dst tensors at gpu-page granularity
    for group_idx, dst_to_src in enumerate(dst_to_src_per_group):
        group_tensor_offset = group_idx * tensors_per_group
        for tensor_idx in range(tensors_per_group):
            src_tensor = handler.src_tensors[group_tensor_offset + tensor_idx]
            dst_tensor = handler.dst_tensors[group_tensor_offset + tensor_idx]
            orig_dst_tensor = orig_dst_tensors[group_tensor_offset + tensor_idx]
            src_view = src_tensor.view(-1, gpu_page_size_bytes)
            dst_view = dst_tensor.view(-1, gpu_page_size_bytes)
            orig_dst_view = orig_dst_tensor.view(-1, gpu_page_size_bytes)
            for dst_sub_block in range(num_dst_sub_blocks):
                src_sub_block = dst_to_src.get(dst_sub_block)
                if src_sub_block is not None:
                    expected = src_view[src_sub_block]
                else:
                    expected = orig_dst_view[dst_sub_block]
                torch.testing.assert_close(
                    dst_view[dst_sub_block].cpu(), expected.cpu()
                )

    handlers.cpu_to_gpu_handler.shutdown()
    handlers.gpu_to_cpu_handler.shutdown()
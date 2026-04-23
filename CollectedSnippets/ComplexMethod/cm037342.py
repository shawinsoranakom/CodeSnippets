def init_meta(
        self,
        attn_groups_iter: Iterable["AttentionGroup"],
        kernel_block_sizes: list[int],
        cache_dtype: str,
        runner_only_attn_layers: set[str],
        static_forward_context: dict[str, Any],
    ) -> None:
        """One-time precomputation for zero_block_ids.

        Builds absolute-address table for the Triton zeroing kernel.
        Each entry is the absolute byte address of a segment start on the
        GPU, so segments in different CUDA allocations work correctly.

        Block IDs from the scheduler reference logical blocks whose size
        may differ from the kernel block size (virtual block splitting).
        PAGE_SIZE_EL accounts for this ratio so that
        ``block_id * PAGE_SIZE_EL`` lands at the correct offset.

        Only AttentionSpec layers are processed; Mamba layers are skipped.
        """
        seen_ptrs: set[int] = set()
        seg_addrs: list[int] = []
        page_size_el: int | None = None

        for group in attn_groups_iter:
            spec = group.kv_cache_spec
            if not isinstance(spec, FullAttentionSpec):
                continue
            if group.kv_cache_group_id >= len(kernel_block_sizes):
                continue
            kernel_bs = kernel_block_sizes[group.kv_cache_group_id]
            ratio = spec.block_size // kernel_bs
            block_dim = group.backend.get_kv_cache_block_dim(
                kernel_bs,
                spec.num_kv_heads,
                spec.head_size,
                cache_dtype_str=cache_dtype,
            )

            for layer_name in group.layer_names:
                if layer_name in runner_only_attn_layers:
                    continue
                kv = static_forward_context[layer_name].kv_cache
                if not isinstance(kv, torch.Tensor):
                    continue
                dp = kv.data_ptr()
                if dp in seen_ptrs:
                    continue
                seen_ptrs.add(dp)

                el = kv.element_size()
                cur_bytes = kv.stride(block_dim) * el
                assert cur_bytes % 4 == 0
                kernel_block_el = cur_bytes // 4
                cur_page_el = kernel_block_el * ratio
                if page_size_el is None:
                    page_size_el = cur_page_el
                else:
                    assert page_size_el == cur_page_el, (
                        f"Non-uniform page sizes: {page_size_el} vs {cur_page_el}"
                    )

                block_stride_bytes = cur_bytes
                outer_dims = [
                    d
                    for d in range(block_dim)
                    if kv.stride(d) * el > block_stride_bytes
                ]
                outer_strides = [kv.stride(d) * el for d in outer_dims]
                for outer in iprod(*(range(kv.shape[d]) for d in outer_dims)):
                    off_bytes = sum(i * s for i, s in zip(outer, outer_strides))
                    seg_addrs.append(dp + off_bytes)

        if not seg_addrs or page_size_el is None:
            self._meta = None
            return

        blk_size = min(largest_power_of_2_divisor(page_size_el), 1024)
        self._id_cap = 8192
        self._ids_pinned = torch.empty(
            self._id_cap,
            dtype=torch.int64,
            pin_memory=self.pin_memory,
        )
        self._ids_gpu = torch.empty(self._id_cap, dtype=torch.int64, device=self.device)
        self._meta = (
            torch.tensor(seg_addrs, dtype=torch.uint64, device=self.device),
            page_size_el,
            blk_size,
            len(seg_addrs),
        )
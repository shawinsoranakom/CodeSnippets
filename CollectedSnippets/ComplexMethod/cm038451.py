def _build_mamba_info(
        self,
        remote_tp_size: int,
        remote_block_size: int,
        remote_block_len: int,
        remote_physical_blocks_per_logical: int,
        local_block_len: int,
    ) -> MambaEngineTransferInfo:
        """Compute Mamba transfer plan."""
        K = self.total_num_kv_heads
        local_tp = self.tp_size
        local_rank = self.tp_rank

        is_remote_replicated = remote_tp_size > K
        remote_physical_heads = max(1, K // remote_tp_size)

        if local_tp >= remote_tp_size:
            assert local_tp % remote_tp_size == 0
            tp_ratio = local_tp // remote_tp_size
        else:
            assert remote_tp_size % local_tp == 0
            tp_ratio = -(remote_tp_size // local_tp)

        abs_tp = -tp_ratio if tp_ratio < 0 else 1

        mamba_range: range | None = None
        if tp_ratio < 0:
            mamba_range = range(local_rank * abs_tp, (local_rank + 1) * abs_tp)

        # ---- FA read targets ----
        if self.is_mla or tp_ratio >= 0:
            num_fa_reads = 1
            fa_source_ranks: list[int] = (
                [0]
                if self.is_mla
                else [local_rank // tp_ratio if tp_ratio > 0 else local_rank]
            )
        else:
            local_needs = self._physical_head_range(local_tp, K, local_rank)
            search_range = (
                mamba_range if mamba_range is not None else range(remote_tp_size)
            )
            seen: set[tuple[int, int]] = set()
            fa_source_ranks = []
            for p in search_range:
                p_has = self._physical_head_range(remote_tp_size, K, p)
                ov = self._range_overlap(local_needs, p_has)
                if len(ov) > 0:
                    key = (ov.start, ov.stop)
                    if key not in seen:
                        seen.add(key)
                        fa_source_ranks.append(p)
            if not fa_source_ranks:
                for p in range(remote_tp_size):
                    p_has = self._physical_head_range(remote_tp_size, K, p)
                    ov = self._range_overlap(local_needs, p_has)
                    if len(ov) > 0:
                        key = (ov.start, ov.stop)
                        if key not in seen:
                            seen.add(key)
                            fa_source_ranks.append(p)
            num_fa_reads = len(fa_source_ranks)

        # ---- All source ranks (mamba + FA) ----
        if mamba_range is not None and abs_tp > num_fa_reads:
            num_mamba_reads = abs_tp
            all_source_ranks = list(mamba_range)
        else:
            num_mamba_reads = num_fa_reads
            all_source_ranks = list(fa_source_ranks)

        # ---- FA descriptor bytes ----
        effective_block_len = min(local_block_len, remote_block_len)
        if self.is_kv_layout_blocks_first:
            fa_descriptor_bytes = effective_block_len // 2
        else:
            fa_descriptor_bytes = effective_block_len

        # ---- Validation ----
        is_local_replicated = local_tp > K
        if is_local_replicated and is_remote_replicated and tp_ratio > 0:
            logger.info(
                "Both-replicated hetero-TP: local_tp=%d > remote_tp=%d > K=%d.",
                local_tp,
                remote_tp_size,
                K,
            )
        tt_set = set(all_source_ranks)
        for t in fa_source_ranks:
            if t not in tt_set:
                logger.error(
                    "FA source rank %d NOT in all_source_ranks %s.",
                    t,
                    all_source_ranks,
                )
        if self.is_kv_layout_blocks_first and tp_ratio < 0 and num_fa_reads > 0:
            local_k_half = local_block_len // 2
            remote_k_half = remote_block_len // 2
            expected = local_k_half // num_fa_reads
            if expected != remote_k_half:
                logger.warning(
                    "FA size mismatch: local_k_half=%d / reads=%d = %d, "
                    "but remote_k_half=%d.",
                    local_k_half,
                    num_fa_reads,
                    expected,
                    remote_k_half,
                )

        return MambaEngineTransferInfo(
            remote_tp_size=remote_tp_size,
            remote_block_len=remote_block_len,
            remote_block_size=remote_block_size,
            remote_physical_blocks_per_logical=(remote_physical_blocks_per_logical),
            remote_fa_source_ranks=tuple(fa_source_ranks),
            remote_all_source_ranks=tuple(all_source_ranks),
            remote_num_fa_reads=num_fa_reads,
            remote_num_mamba_reads=num_mamba_reads,
            remote_fa_descriptor_bytes=fa_descriptor_bytes,
            is_remote_replicated=is_remote_replicated,
            remote_physical_heads=remote_physical_heads,
        )
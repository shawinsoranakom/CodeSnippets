def _build_fa_remote_for_mamba(
        self,
        nixl_agent_meta: NixlAgentMetadata,
        block_size_ratio: int,
        transfer_topo: TransferTopology,
        remote_engine_id: EngineId,
    ) -> list[tuple[int, int, int]]:
        """Build remote FA descriptors for mamba models.

        Uses TransferTopology for GQA-aware FA divisor and head-based rank
        offset instead of the standard uniform tp_ratio split.
        """
        assert block_size_ratio == 1, (
            "Mamba 3-read transfer with block_size_ratio != 1 is not tested. "
            f"Got block_size_ratio={block_size_ratio}."
        )
        # TODO (ZhanqiuHu): unify with register_remote_blocks when Mamba-HMA
        # hetero-TP logic stabilizes.
        mamba_info = transfer_topo.get_engine_info(remote_engine_id)
        assert isinstance(mamba_info, MambaEngineTransferInfo)
        tp_ratio = transfer_topo.tp_ratio(mamba_info.remote_tp_size)
        result: list[tuple[int, int, int]] = []
        for i, base_addr in enumerate(nixl_agent_meta.kv_caches_base_addr):
            local_block_len = self.get_backend_aware_kv_block_len(
                layer_idx=i, first_split=True, mamba_view=False
            )
            remote_kv_block_len = local_block_len // block_size_ratio
            if block_size_ratio > 1:
                local_block_len = remote_kv_block_len

            if tp_ratio < 0 and not self.use_mla:
                local_block_len = local_block_len // mamba_info.remote_num_fa_reads

            rank_offset = transfer_topo.fa_rank_offset(
                remote_engine_id, remote_kv_block_len
            )

            num_blocks = nixl_agent_meta.num_blocks
            page_size = nixl_agent_meta.block_lens[i]
            for block_id in range(num_blocks):
                block_offset = block_id * page_size
                addr = base_addr + block_offset + rank_offset
                result.append((addr, local_block_len, nixl_agent_meta.device_id))

            if transfer_topo.is_kv_layout_blocks_first:
                second_split = self.get_backend_aware_kv_block_len(
                    layer_idx=i, first_split=False, mamba_view=False
                )
                if tp_ratio < 0 and not self.use_mla:
                    second_split = second_split // mamba_info.remote_num_fa_reads
                for block_id in range(num_blocks):
                    block_offset = block_id * page_size
                    addr = base_addr + block_offset + rank_offset
                    v_addr = addr + nixl_agent_meta.block_lens[i] // 2
                    result.append((v_addr, second_split, nixl_agent_meta.device_id))
        return result
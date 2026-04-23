def _validate_remote_agent_handshake(
        self, nixl_agent_meta: NixlAgentMetadata, remote_tp_size: int
    ):
        """
        Validate the remote agent handshake metadata ensuring the
        invariants hold true.
        """
        remote_engine_id = nixl_agent_meta.engine_id

        assert self.transfer_topo is not None
        remote_info = self.transfer_topo.get_engine_info(remote_engine_id)
        assert remote_info.remote_tp_size == remote_tp_size

        tp_ratio = self.transfer_topo.tp_ratio(remote_tp_size)
        block_size_ratio = self.transfer_topo.block_size_ratio(
            nixl_agent_meta.block_size
        )
        # num_kv_heads > tp_size with P_TP > D_TP not supported for non-mamba.
        # Mamba models can have replicated FA KV with tp_ratio < 0.
        if not self._has_mamba:
            assert not (
                tp_ratio < 0 and self.transfer_topo.is_kv_replicated(remote_engine_id)
            )

        if self._is_hma_required:
            assert block_size_ratio == 1, (
                "HMA does not support different remote block size yet"
            )
        kv_cache_layout = (
            self.kv_cache_layout
            if not self.use_host_buffer
            else self.host_buffer_kv_cache_layout
        )
        if not self.use_mla and nixl_agent_meta.kv_cache_layout != kv_cache_layout:
            if (
                self.kv_transfer_config.enable_permute_local_kv
                and nixl_agent_meta.kv_cache_layout == "HND"
            ):
                logger.info(
                    "Remote is HND and local is NHD, enabled additional permute "
                    "on local device KV."
                )
                assert not self._is_hma_required, (
                    "HMA does not support block size post processing"
                )
                self.enable_permute_local_kv = True
            else:
                raise RuntimeError(
                    "Heterogeneous TP expects same kv_cache_layout. "
                    "Or enable experimental feature to use HND to NHD support by "
                    "setting 'enable_permute_local_kv'=True in --kv-transfer-config."
                )
        # if remote_agent used attn is not same as local,
        # hint heterogenuous attn post process
        if (
            nixl_agent_meta.attn_backend_name != self.backend_name
            and self.backend_name in ["CPU_ATTN"]
        ):
            if self._is_hma_required:
                raise RuntimeError(
                    "heterogeneous attn post process is not supported with HMA"
                )
            logger.info(
                "[Experimental] CPU_ATTN backend is used, "
                "hint heterogeneous attn post process"
            )
            self.enable_heterogeneous_attn_post_process = True

        # Heterogeneous TP requires head-splitting, which only works with
        # HND layout. MLA and replicated-KV cases don't split on heads.
        # Mamba doesn't support heterogeneous TP.
        if (
            abs(tp_ratio) != 1
            and not self.use_mla
            and not self.transfer_topo.is_kv_replicated(remote_engine_id)
            and kv_cache_layout != "HND"
            and not self.enable_permute_local_kv
        ):
            raise RuntimeError(
                "Heterogeneous TP head-dimension splitting requires contiguous heads. "
                "Use HND layout on the prefill side."
            )

        # Block len can only vary across layers when using MLA.
        remote_block_len = nixl_agent_meta.block_lens[0]
        if self.use_mla or self.transfer_topo.is_kv_replicated(remote_engine_id):
            # With replicated KV cache, only the number of blocks can differ.
            # TODO (ZhanqiuHu): For mamba models, validate FA and mamba
            # block_lens separately.
            if not self._has_mamba:
                for i in range(len(self.block_len_per_layer)):
                    assert (
                        self.block_len_per_layer[i] // block_size_ratio
                        == nixl_agent_meta.block_lens[i]
                    ), "KV cache sizes must match between P and D when replicated"
        else:
            # When MLA is not used, this is a list of the same block length
            for block_len in nixl_agent_meta.block_lens:
                assert block_len == remote_block_len, (
                    "All remote layers must have the same block size"
                )

            # HMA hybrid models (mamba+attention) pad block_len to
            # max(attn_page, mamba_page), so the linear tp_ratio scaling
            # assumption only holds for pure-attention models.
            if not self._has_mamba:
                if tp_ratio > 0:
                    assert (
                        remote_block_len
                        == (self.block_len_per_layer[0] * tp_ratio) // block_size_ratio
                    ), (
                        "Remote P worker KV layer cache must be of shape [2, N,"
                        " local_kv_heads*tp_ratio, page_size, head_dim] and "
                        "same dtype."
                    )
                else:
                    assert block_size_ratio == 1, (
                        "Different local/remote block sizes are not supported"
                        " when P TP > D TP."
                    )
                    assert remote_block_len == self.block_len_per_layer[0] // (
                        -tp_ratio
                    ), (
                        "Remote P worker KV layer cache must be of shape [2, N,"
                        " local_kv_heads/tp_ratio, page_size, head_dim] and "
                        "same dtype."
                    )

        # TP workers that handhshake with same remote have same #blocks.
        assert self.dst_num_blocks[remote_engine_id] == nixl_agent_meta.num_blocks
        # Same number of regions/~layers.
        assert len(nixl_agent_meta.kv_caches_base_addr) == len(self.block_len_per_layer)
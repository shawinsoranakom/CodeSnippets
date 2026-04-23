def register_kv_caches(self, kv_caches: dict[str, torch.Tensor]):
        """Register the KV Cache data in nixl."""
        self.transfer_topo = TransferTopology(
            tp_rank=self.tp_rank,
            tp_size=self.world_size,
            block_size=self.block_size,
            engine_id=self.engine_id,
            is_mla=self.use_mla,
            total_num_kv_heads=self.model_config.get_total_num_kv_heads(),
            attn_backends=self.attn_backends,
            # SSM States come in tuples (ssm, conv)
            tensor_shape=next(iter(kv_caches.values())).shape
            if not self._has_mamba
            else None,
            is_mamba=self._has_mamba,
        )
        self.compat_hash = compute_nixl_compatibility_hash(
            self.vllm_config, self.backend_name, self.transfer_topo.cross_layers_blocks
        )

        if self.use_host_buffer:
            self.initialize_host_xfer_buffer(kv_caches=kv_caches)
            assert len(self.host_xfer_buffers) == len(kv_caches), (
                f"host_buffer: {len(self.host_xfer_buffers)}, "
                f"kv_caches: {len(kv_caches)}"
            )
            xfer_buffers = self.host_xfer_buffers
        else:
            xfer_buffers = kv_caches
            assert not self.host_xfer_buffers, (
                "host_xfer_buffer should not be initialized when "
                f"kv_buffer_device is {self.kv_buffer_device}"
            )

        logger.info(
            "Registering KV_Caches. use_mla: %s, kv_buffer_device: %s, "
            "use_host_buffer: %s",
            self.use_mla,
            self.kv_buffer_device,
            self.use_host_buffer,
        )

        caches_data = []
        # With hybrid allocator, layers can share a kv cache tensor
        seen_base_addresses = []

        # Note(tms): I modified this from the original region setup code.
        # K and V are now in different regions. Advantage is that we can
        # elegantly support MLA and any cases where the K and V tensors
        # are non-contiguous (it's not locally guaranteed that they will be)
        # Disadvantage is that the encoded NixlAgentMetadata is now larger
        # (roughly 8KB vs 5KB).
        # Conversely for FlashInfer, K and V are registered in the same region
        # to better exploit the memory layout (ie num_blocks is the first dim).
        tensor_size_bytes = None

        # Enable different block lengths for different layers *only* when MLA is used.
        # This is not used for SSM layers, which use the counterpart `mamba_ssm_size`.
        self.block_len_per_layer = list[int]()
        for layer_name, cache_or_caches in xfer_buffers.items():
            # NOTE (NickLucche) Hybrid SSM models assume a layout that is similar to
            # that of FI, with block laid out as in `get_backend_aware_kv_block_len`.
            # However, physical page_size may differ when kernel requires a specific
            # block size. This leads to SSM and FA layers having different num_blocks.
            # `_physical_blocks_per_logical_kv_block` ratio is used to adjust for this.
            layer_spec = self._layer_specs[layer_name]
            if isinstance(layer_spec, UniformTypeKVCacheSpecs):
                # MLA DSv32 Indexer case: UniformTypeKVCacheSpecs merges kv_cache_specs
                layer_spec = layer_spec.kv_cache_specs[layer_name]
            cache_list = self.transfer_topo.get_transfer_cache_regions(
                cache_or_caches, layer_spec
            )
            # `layer_spec.page_size_bytes` only accounts for logical page_size, that is
            # the page_size assuming constant `self._logical_num_blocks`.
            physical_page_size = (
                layer_spec.page_size_bytes
                if isinstance(layer_spec, MambaSpec)
                else layer_spec.page_size_bytes
                // self._physical_blocks_per_logical_kv_block
            )
            # For when registering multiple tensors eg K/V in separate regions.
            physical_page_size = physical_page_size // len(cache_list)
            if self.transfer_topo._cross_layers_blocks:
                # When cross-layers blocks are used, multiply by number of layers
                physical_page_size = physical_page_size * len(
                    self.kv_cache_config.kv_cache_tensors
                )
            num_blocks = (
                self._logical_num_blocks
                if isinstance(layer_spec, MambaSpec)
                else self.num_blocks
            )
            # `page_size` accounts for physical blocks, st KVCache is always
            # [`num_blocks` * `page_size`]
            curr_tensor_size_bytes = num_blocks * physical_page_size
            if tensor_size_bytes is None:
                tensor_size_bytes = curr_tensor_size_bytes

            # TODO (NickLucche) we could eventually unify how we handle FA/FI regions,
            # registering a single tensor for both K/V and splitting logically like FI.
            for cache in cache_list:
                base_addr = cache.data_ptr()
                if base_addr in seen_base_addresses:
                    # NOTE (NickLucche) HMA employs memory pooling to share tensors
                    # across groups. This results in skipping all tensors but the ones
                    # pointed to by group0. Also, generally we will have more blocks
                    # per tensor but fewer regions.
                    logger.debug("Skipping %s because it's already seen", layer_name)
                    continue
                logger.debug(
                    "Registering layer %s with cache shape: %s", layer_name, cache.shape
                )
                seen_base_addresses.append(base_addr)
                # Only record non-Mamba page sizes.
                if isinstance(layer_spec, MambaSpec):
                    self.block_len_per_layer.append(
                        physical_page_size // self._physical_blocks_per_logical_kv_block
                    )
                else:
                    self.block_len_per_layer.append(physical_page_size)

                assert cache.shape[0] == num_blocks, (
                    "All kv cache tensors must have the same number of blocks"
                )

                if not self.use_mla:
                    # Different kv cache shape is not supported by HeteroTP.
                    # This must also hold true for Mamba-like models.
                    assert tensor_size_bytes == curr_tensor_size_bytes, (
                        "All kv cache tensors must have the same size"
                    )
                # Need to make sure the device ID is non-negative for NIXL,
                # Torch uses -1 to indicate CPU tensors.
                self.device_id = max(cache.get_device(), 0)
                caches_data.append(
                    (base_addr, curr_tensor_size_bytes, self.device_id, "")
                )

        logger.debug(
            "Different block lengths collected: %s", set(self.block_len_per_layer)
        )
        assert len(self.block_len_per_layer) == len(seen_base_addresses)

        self.kv_caches_base_addr[self.engine_id][self.tp_rank] = seen_base_addresses
        self.num_regions = len(caches_data)

        if self.transfer_topo.is_kv_layout_blocks_first:
            # NOTE (NickLucche) When FlashInfer is used, memory is registered
            # with joint KV for each block. This minimizes the overhead in
            # registerMem allowing faster descs queries. In order to be able to
            # split on kv_heads dim as required by heterogeneous TP, one must
            # be able to index K/V separately. Hence we double the number
            # of 'virtual' regions here and halve `block_len` below.
            # Similarly for Mamba layers, we register SSM+Conv as a single region and
            # then duplicate it logically to be able to index SSM/Conv separately.
            self.num_regions *= 2

        # Total local FA descriptors (boundary between FA and mamba descs).
        self.num_descs = self.num_regions * self.num_blocks

        descs = self.nixl_wrapper.get_reg_descs(caches_data, self.nixl_memory_type)
        logger.debug("Registering descs: %s", caches_data)
        self.nixl_wrapper.register_memory(descs, backends=self.nixl_backends)
        logger.debug("Done registering descs")
        self._registered_descs.append(descs)

        self.device_kv_caches = kv_caches
        self.dst_num_blocks[self.engine_id] = self.num_blocks

        if self._has_mamba:
            self._physical_blocks_per_logical[self.engine_id] = (
                self._physical_blocks_per_logical_kv_block
            )
            logger.info(
                "Hybrid SSM registration: num_blocks=%s, "
                "logical_num_blocks=%s, ratio=%s, num_regions=%s, "
                "num_descs=%s, mamba_ssm_size=%s, block_len_per_layer=%s",
                self.num_blocks,
                self._logical_num_blocks,
                self._physical_blocks_per_logical_kv_block,
                self.num_regions,
                self.num_descs,
                self._mamba_ssm_size,
                set(self.block_len_per_layer),
            )

        # Register local/src descr for NIXL xfer.
        self.src_xfer_handles_by_block_size[self.block_size], self.src_blocks_data = (
            self.register_local_xfer_handler(self.block_size)
        )

        # After KV Caches registered, listen for new connections.
        agent_metadata = NixlAgentMetadata(
            engine_id=self.engine_id,
            agent_metadata=self.nixl_wrapper.get_agent_metadata(),
            device_id=self.device_id,
            kv_caches_base_addr=self.kv_caches_base_addr[self.engine_id][self.tp_rank],
            num_blocks=self.num_blocks,
            block_lens=self.block_len_per_layer,
            kv_cache_layout=self.kv_cache_layout
            if not self.use_host_buffer
            else self.host_buffer_kv_cache_layout,
            block_size=self.block_size,
            ssm_sizes=self._mamba_ssm_size,
            attn_backend_name=self.backend_name,
        )
        # Wrap metadata in payload with hash for defensive decoding
        assert self.compat_hash is not None
        encoder = msgspec.msgpack.Encoder()
        self.xfer_handshake_metadata = NixlHandshakePayload(
            compatibility_hash=self.compat_hash,
            agent_metadata_bytes=encoder.encode(agent_metadata),
        )
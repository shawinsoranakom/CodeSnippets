def register_kv_caches(self, kv_caches: dict[str, torch.Tensor]):
        """Register the KV Cache data in moriio."""

        _, first_kv_cache = next(iter(kv_caches.items()))
        kv_elem_size = first_kv_cache.element_size()

        use_mla = len(first_kv_cache.shape) == 3
        assert use_mla == self.use_mla

        if use_mla:
            # MLA case.
            self.num_blocks = first_kv_cache.shape[0]
            block_rank = 2  # [block_size, latent_dim]
            block_shape = first_kv_cache.shape[-block_rank:]
            block_size, kv_latent_dim = block_shape
            self.slot_size_bytes = kv_elem_size * kv_latent_dim
        else:
            # [2 (k and v), num_blocks, ...]
            self.num_blocks = first_kv_cache.shape[1]
            block_rank = 3  # [block_size, kv_heads, head_dim]
            block_shape = first_kv_cache.shape[-block_rank:]
            block_size, n_kv_heads, head_dim = block_shape[-3:]
            # head size in bytes.
            self.slot_size_bytes = (
                kv_elem_size * n_kv_heads * head_dim
            )  # 1 token 1 layer size , slot size
        assert block_size == self.block_size
        # TODO(tms): self.block_len needs to be per-layer for sliding window,
        # hybrid attn, etc
        # block size in bytes
        self.block_len = kv_elem_size * math.prod(block_shape)
        self.kv_cache_shape = first_kv_cache.shape
        self.block_shape = block_shape
        self.kv_element_size = kv_elem_size

        self.dst_num_blocks[self.engine_id] = self.num_blocks
        self.kv_caches = kv_caches  # layer name to kv cache
        kv_caches_base_addr = []
        caches_data = []

        for cache_or_caches in kv_caches.values():
            cache_list = [cache_or_caches] if use_mla else cache_or_caches
            for cache in cache_list:
                base_addr = cache.data_ptr()
                region_len = self.num_blocks * self.block_len
                caches_data.append((base_addr, region_len, cache.device.index, ""))
                kv_caches_base_addr.append(base_addr)

        for layer_name, kv_cache in kv_caches.items():
            if layer_name not in self.layer_name_to_local_kv_cache_metadata:
                self.layer_name_to_local_kv_cache_metadata[layer_name] = []

            moriio_mem_metadata = self.moriio_wrapper.register_local_tensor(kv_cache)
            self.layer_name_to_local_kv_cache_metadata[layer_name].append(
                moriio_mem_metadata
            )

            self.local_kv_cache_size.append(cache.nelement() * cache.element_size())

        self.kv_caches_base_addr[self.engine_id] = kv_caches_base_addr
        self.num_regions = len(caches_data)
        self.num_layers = len(self.kv_caches.keys())

        # Optimization for models with local attention (Llama 4)
        if self.vllm_config.model_config.hf_config.model_type == "llama4":
            from transformers import Llama4TextConfig

            assert isinstance(
                self.vllm_config.model_config.hf_text_config, Llama4TextConfig
            )
            llama4_config = self.vllm_config.model_config.hf_text_config
            no_rope_layers = llama4_config.no_rope_layers
            chunk_size = llama4_config.attention_chunk_size
            chunk_block_size = math.ceil(chunk_size / self.block_size)
            for layer_idx in range(self.num_layers):
                # no_rope_layers[layer_idx] == 0 means NoPE (global)
                # Any other value means RoPE (local chunked)
                is_local_attention = no_rope_layers[layer_idx] != 0
                block_window = chunk_block_size if is_local_attention else None
                self.block_window_per_layer.append(block_window)
            logger.debug(
                "Llama 4 block window per layer mapping: %s",
                self.block_window_per_layer,
            )
            assert len(self.block_window_per_layer) == self.num_layers

        metadata = MoRIIOAgentMetadata(
            engine_id=self.engine_id,
            agent_metadata=self.moriio_wrapper.get_agent_metadata(),
            kv_caches_base_addr=self.kv_caches_base_addr[self.engine_id],
            num_blocks=self.num_blocks,
            block_len=self.block_len,
            attn_backend_name=self.backend_name,
        )
        ready_event = threading.Event()
        self._moriio_handshake_listener_t = threading.Thread(
            target=self._moriio_handshake_listener,
            args=(
                metadata,
                ready_event,
                self.side_channel_port,
                self.tp_rank,
                self.dp_rank,
                self.layer_name_to_local_kv_cache_metadata,
            ),
            daemon=True,
            name="moriio_handshake_listener",
        )
        self._moriio_handshake_listener_t.start()
        ready_event.wait()  # Wait for listener ZMQ socket to be ready.
        self.moriio_wrapper.async_wait_reqid()
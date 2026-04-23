def register_kv_caches(self, kv_caches: dict[str, torch.Tensor]):
        """Register the KV Cache data in mooncake."""

        logger.info("Registering KV_Caches. use_mla: %s", self.use_mla)

        kv_data_ptrs = []
        kv_data_lens = []
        seen_base_addresses = []
        self.block_len_per_layer = []

        split_k_and_v = self.transfer_topo.split_k_and_v
        tensor_size_bytes = None
        for layer_name, cache_or_caches in kv_caches.items():
            cache_list = cache_or_caches if split_k_and_v else [cache_or_caches]
            logger.debug(
                "registering layer %s with %d cache tensor(s)",
                layer_name,
                len(cache_list),
            )

            for cache in cache_list:
                self._log_debug_cache_registration(layer_name, cache)
                base_addr = cache.data_ptr()
                if base_addr in seen_base_addresses:
                    continue

                seen_base_addresses.append(base_addr)
                curr_tensor_size_bytes = cache.nbytes

                if tensor_size_bytes is None:
                    tensor_size_bytes = curr_tensor_size_bytes
                    self.num_blocks = cache.shape[0]
                assert cache.shape[0] == self.num_blocks, (
                    "All kv cache tensors must have the same number of blocks"
                )
                assert curr_tensor_size_bytes % self.num_blocks == 0, (
                    "Mooncake expects each kv cache tensor size to be "
                    "divisible by the number of blocks."
                )
                self.block_len_per_layer.append(
                    curr_tensor_size_bytes // self.num_blocks
                )
                kv_data_ptrs.append(base_addr)
                kv_data_lens.append(curr_tensor_size_bytes)

        self.kv_caches_base_addr = seen_base_addresses
        self.seen_base_addresses = seen_base_addresses

        ret_value = self.engine.batch_register_memory(kv_data_ptrs, kv_data_lens)
        if ret_value != 0:
            raise RuntimeError("Mooncake batch memory registration failed.")

        assert tensor_size_bytes is not None
        assert self.num_blocks != 0
        self.device_kv_caches = kv_caches
        logger.debug(
            "registered num_blocks=%d block_lens=%s",
            self.num_blocks,
            self.block_len_per_layer,
        )

        # No need to launch server for D node.
        if self.is_kv_consumer:
            return

        ready_event = threading.Event()
        asyncio.run_coroutine_threadsafe(
            self._mooncake_sender_listener(ready_event), self.sender_loop
        )
        ready_event.wait()
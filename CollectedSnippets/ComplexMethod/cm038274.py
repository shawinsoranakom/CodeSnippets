def post_init(self):
        """Allocate static buffer pool and start initial prefetches.

        Note: Parameters have already been offloaded to CPU during wrap_modules()
        (in _CpuParamOffloader.__init__), so GPU memory is available for the
        static buffer pool.
        """
        # Sync CPU storage with current param.data BEFORE collecting param info.
        # This is needed because process_weights_after_loading may have:
        # 1. Transformed weights (quantization, transpose, etc.)
        # 2. Created new CPU tensors via device_loading_context
        # Our _cpu_storage would be stale otherwise.
        for offloader in self.module_offloaders:
            offloader.sync_cpu_storage()

        # Collect parameter info (now using synced CPU storage)
        param_infos: list[ParamInfo] = []
        device: torch.device | None = None

        for offloader in self.module_offloaders:
            param_infos.extend(offloader.get_param_infos())
            if device is None:
                device = offloader.device

        if device is None:
            # No modules to offload
            return

        # Allocate static buffer pool
        self.buffer_pool = StaticBufferPool(
            param_infos=param_infos,
            slot_capacity=self.prefetch_step,
            device=device,
        )

        # Assign buffer slots and point parameters to GPU buffers
        for idx, offloader in enumerate(self.module_offloaders):
            slot_idx = idx % self.prefetch_step
            offloader.assign_buffer_slot(self.buffer_pool, slot_idx)

        # Collect offloaded bytes
        for offloader in self.module_offloaders:
            offloader.post_init()
            self.total_offloaded_bytes += offloader.offloaded_bytes

        logger.info_once(
            f"[PrefetchOffloader] Initialized {len(self.module_offloaders)} modules. "
            f"Total GPU memory saved: {self.total_offloaded_bytes / 1e9:.4f} GB, "
            f"Static buffer pool: {self.buffer_pool.total_bytes / 1e9:.4f} GB "
            f"(group_size={self.group_size}, num_in_group={self.num_in_group}, "
            f"prefetch_step={self.prefetch_step}, mode={self.mode})"
        )

        # Start initial prefetches
        for i in range(min(self.prefetch_step, len(self.module_offloaders))):
            self.module_offloaders[i].start_onload_to_static()
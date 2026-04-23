def wake_up(self, tags: list[str] | None = None) -> None:
        from vllm.device_allocator.cumem import CuMemAllocator

        allocator = CuMemAllocator.get_instance()
        allocator.wake_up(tags)

        # Restore the buffers after level 2 sleep
        if len(self._sleep_saved_buffers):
            model = self.model_runner.model
            for name, buffer in model.named_buffers():
                if name in self._sleep_saved_buffers:
                    buffer.data.copy_(self._sleep_saved_buffers[name].data)
            self._sleep_saved_buffers = {}

        # If the KV cache has just been woken up,
        # the internal state of cache_engine must be reset,
        # especially the FP8 scaling factor.
        if (
            (tags is None or "kv_cache" in tags)
            and is_quantized_kv_cache(self.cache_config.cache_dtype)
            and hasattr(self.model_runner, "init_fp8_kv_scales")
        ):
            self.model_runner.init_fp8_kv_scales()
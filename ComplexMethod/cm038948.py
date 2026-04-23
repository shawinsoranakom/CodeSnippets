def tune(
        self,
        num_tokens: int,
        num_experts: int,
        shard_intermediate_size: int,
        hidden_size: int,
        topk: int,
        dtype: torch.dtype,
        use_fp8_w8a8: bool,
        use_int8_w8a16: bool,
        use_int4_w4a16: bool,
        search_space: list[dict[str, int]],
        block_quant_shape: list[int],
        use_deep_gemm: bool,
    ) -> dict[str, int]:
        # local import to allow serialization by ray
        from vllm.platforms import current_platform

        best_config = None
        best_time = float("inf")
        if current_platform.is_rocm():
            is_fp16 = not (use_fp8_w8a8 or use_int8_w8a16 or use_int4_w4a16)
            search_space = prune_rocm_search_space(
                num_tokens,
                shard_intermediate_size,
                hidden_size,
                search_space,
                is_fp16,
                topk,
            )

        need_device_guard = False
        if current_platform.is_rocm():
            visible_device = os.environ.get("ROCR_VISIBLE_DEVICES", None)
            if visible_device != f"{self.device_id}":
                need_device_guard = True

        with (
            # Ray restricts each worker to one GPU; use local index 0
            torch.accelerator.device_index(0) if need_device_guard else nullcontext()
        ):
            for idx, config in enumerate(tqdm(search_space)):
                try:
                    kernel_time = benchmark_config(
                        config,
                        num_tokens,
                        num_experts,
                        shard_intermediate_size,
                        hidden_size,
                        topk,
                        dtype,
                        use_fp8_w8a8,
                        use_int8_w8a16,
                        use_int4_w4a16,
                        num_iters=20,
                        block_quant_shape=block_quant_shape,
                        use_deep_gemm=use_deep_gemm,
                    )
                except triton.runtime.autotuner.OutOfResources:
                    # Some configurations may be invalid and fail to compile.
                    continue

                if kernel_time < best_time:
                    best_time = kernel_time
                    best_config = config

                # Periodically clear Triton JIT cache to prevent OOM
                # This is especially important for large models with many experts
                if (
                    TRITON_CACHE_CLEAR_INTERVAL > 0
                    and idx > 0
                    and idx % TRITON_CACHE_CLEAR_INTERVAL == 0
                ):
                    clear_triton_cache()

        # Final cleanup after tuning completes
        clear_triton_cache()

        now = datetime.now()
        print(f"{now.ctime()}] Completed tuning for batch_size={num_tokens}")
        assert best_config is not None
        return best_config
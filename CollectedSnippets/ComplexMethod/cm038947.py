def main(args: argparse.Namespace):
    print(args)

    config = get_config(model=args.model, trust_remote_code=args.trust_remote_code)
    if args.model_prefix:
        config = getattr(config, args.model_prefix)
    E, topk, intermediate_size, hidden_size = get_model_params(config)
    enable_ep = bool(args.enable_expert_parallel)
    if enable_ep:
        ensure_divisibility(E, args.tp_size, "Number of experts")
        E = E // args.tp_size
        shard_intermediate_size = 2 * intermediate_size
    else:
        ensure_divisibility(intermediate_size, args.tp_size, "intermediate_size")
        shard_intermediate_size = 2 * intermediate_size // args.tp_size
    dtype = resolve_dtype(config)
    use_fp8_w8a8 = args.dtype == "fp8_w8a8"
    use_int8_w8a16 = args.dtype == "int8_w8a16"
    use_int4_w4a16 = args.dtype == "int4_w4a16"
    block_quant_shape = get_weight_block_size_safety(config)
    if use_int4_w4a16:
        group_size = get_quantization_group_size(config)
        if group_size is None:
            raise ValueError(
                "Could not determine group_size from model config. "
                "The model's quantization_config must contain a 'group_size' "
                "field (AWQ/GPTQ) or 'config_groups.*.weights.group_size' "
                "(compressed-tensors)."
            )
        # For int4_w4a16, block_shape = [0, group_size]
        # block_shape[0]=0 means no block quantization on N dimension
        block_quant_shape = [0, group_size]

    if args.batch_size is None:
        batch_sizes = [
            1,
            2,
            4,
            8,
            16,
            24,
            32,
            48,
            64,
            96,
            128,
            256,
            512,
            1024,
            1536,
            2048,
            3072,
            4096,
        ]
    else:
        batch_sizes = args.batch_size

    use_deep_gemm = bool(args.use_deep_gemm)

    if current_platform.is_rocm() and "HIP_VISIBLE_DEVICES" in os.environ:
        # Ray will set ROCR_VISIBLE_DEVICES for device visibility
        logger.warning(
            "Ray uses ROCR_VISIBLE_DEVICES to control device accessibility."
            "Replacing HIP_VISIBLE_DEVICES with ROCR_VISIBLE_DEVICES."
        )
        val = os.environ["HIP_VISIBLE_DEVICES"]
        os.environ["ROCR_VISIBLE_DEVICES"] = val
        del os.environ["HIP_VISIBLE_DEVICES"]

    ray.init()
    num_gpus = int(ray.available_resources()["GPU"])
    workers = [BenchmarkWorker.remote(args.seed) for _ in range(num_gpus)]

    def _distribute(method: str, inputs: list[Any]) -> list[Any]:
        outputs = []
        worker_idx = 0
        for input_args in inputs:
            worker = workers[worker_idx]
            worker_method = getattr(worker, method)
            output = worker_method.remote(*input_args)
            outputs.append(output)
            worker_idx = (worker_idx + 1) % num_gpus
        return ray.get(outputs)

    if args.tune:
        # int4_w4a16 weights are uint8-packed, not fp16; treat like fp8 for
        # search space generation (no matrix_instr_nonkdim/kpack exploration).
        is_fp16 = not (use_fp8_w8a8 or use_int8_w8a16 or use_int4_w4a16)
        # For int4_w4a16, the group_size constraint on BLOCK_SIZE_K does not
        # apply: the gptq_awq kernel handles arbitrary BLOCK_SIZE_K regardless
        # of group_size. Skip block_quant_shape filtering to keep the full
        # search space (e.g. BLOCK_SIZE_K=64 with group_size=128).
        tune_block_quant_shape = None if use_int4_w4a16 else block_quant_shape
        search_space = get_configs_compute_bound(is_fp16, tune_block_quant_shape)
        if use_int4_w4a16:
            # SPLIT_K is a required kernel constexpr for gptq_awq kernel;
            # only SPLIT_K=1 is used at runtime, so fix it during tuning.
            for cfg in search_space:
                cfg["SPLIT_K"] = 1
        print(f"Start tuning over {len(search_space)} configurations...")
        if use_deep_gemm:
            raise ValueError(
                "Tuning with --use-deep-gemm is not supported as it only tunes Triton "
                "kernels. Please remove the flag."
            )
        start = time.time()
        configs = _distribute(
            "tune",
            [
                (
                    batch_size,
                    E,
                    shard_intermediate_size,
                    hidden_size,
                    topk,
                    dtype,
                    use_fp8_w8a8,
                    use_int8_w8a16,
                    use_int4_w4a16,
                    search_space,
                    block_quant_shape,
                    use_deep_gemm,
                )
                for batch_size in batch_sizes
            ],
        )
        best_configs = {
            M: sort_config(config) for M, config in zip(batch_sizes, configs)
        }
        save_configs(
            best_configs,
            E,
            shard_intermediate_size,
            hidden_size,
            topk,
            dtype,
            use_fp8_w8a8,
            use_int8_w8a16,
            use_int4_w4a16,
            block_quant_shape,
            args.save_dir,
        )
        end = time.time()
        print(f"Tuning took {end - start:.2f} seconds")
    else:
        outputs = _distribute(
            "benchmark",
            [
                (
                    batch_size,
                    E,
                    shard_intermediate_size,
                    hidden_size,
                    topk,
                    dtype,
                    use_fp8_w8a8,
                    use_int8_w8a16,
                    use_int4_w4a16,
                    block_quant_shape,
                    use_deep_gemm,
                )
                for batch_size in batch_sizes
            ],
        )

        for batch_size, (config, kernel_time) in zip(batch_sizes, outputs):
            print(f"Batch size: {batch_size}, config: {config}")
            print(f"Kernel time: {kernel_time:.2f} us")
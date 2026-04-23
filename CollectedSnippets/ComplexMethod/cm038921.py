def main(args: argparse.Namespace):
    print(args)

    config = AutoConfig.from_pretrained(
        args.model, trust_remote_code=args.trust_remote_code
    )
    if config.architectures[0] == "DbrxForCausalLM":
        E = config.ffn_config.moe_num_experts
        topk = config.ffn_config.moe_top_k
    elif config.architectures[0] == "JambaForCausalLM":
        E = config.num_experts
        topk = config.num_experts_per_tok
    elif (
        config.architectures[0] == "DeepseekV3ForCausalLM"
        or config.architectures[0] == "DeepseekV2ForCausalLM"
        or config.architectures[0] == "Glm4MoeForCausalLM"
        or config.architectures[0] == "Glm4MoeLiteForCausalLM"
    ):
        E = config.n_routed_experts
        topk = config.num_experts_per_tok
    elif config.architectures[0] in ["Qwen2MoeForCausalLM", "Qwen3MoeForCausalLM"]:
        E = config.num_experts
        topk = config.num_experts_per_tok

    else:
        # Support for llama4
        config = config.get_text_config()
        # Default: Mixtral.
        E = config.num_local_experts
        topk = config.num_experts_per_tok

    hidden_size = config.hidden_size
    dtype = torch.float16 if current_platform.is_rocm() else config.dtype
    use_fp8_w8a8 = args.dtype == "fp8_w8a8"
    use_int8_w8a16 = args.dtype == "int8_w8a16"

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
        batch_sizes = [args.batch_size]

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

    outputs = _distribute(
        "benchmark",
        [
            (
                batch_size,
                E,
                hidden_size,
                topk,
                dtype,
                use_fp8_w8a8,
                use_int8_w8a16,
            )
            for batch_size in batch_sizes
        ],
    )

    for batch_size, (permute, unpermute) in zip(batch_sizes, outputs):
        print(f"Batch size: {batch_size}")
        print(f"Permute time: {permute:.2f} us")
        print(f"Unpermute time: {unpermute:.2f} us")
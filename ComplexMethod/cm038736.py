def main(args: argparse.Namespace):
    validate_args(args)
    if args.seed is None:
        args.seed = 0
    random.seed(args.seed)
    # Sample the requests.
    if (
        args.backend == "hf" or args.backend == "mii"
    ) and args.tokenizer_mode == "auto":
        # mistral_common tokenizer is only supported on vllm and vllm-chat backends;
        # for hf and mii backends, we use hf tokenizer
        args.tokenizer_mode = "hf"
    tokenizer = get_tokenizer(
        args.tokenizer,
        tokenizer_mode=args.tokenizer_mode,
        trust_remote_code=args.trust_remote_code,
    )
    requests = get_requests(args, tokenizer)
    is_multi_modal = any(request.multi_modal_data is not None for request in requests)
    request_outputs: list[RequestOutput] | None = None
    if args.backend == "vllm":
        if args.async_engine:
            elapsed_time = uvloop.run(
                run_vllm_async(
                    requests,
                    args.n,
                    AsyncEngineArgs.from_cli_args(args),
                    disable_detokenize=args.disable_detokenize,
                    do_profile=args.profile,
                )
            )
        else:
            elapsed_time, request_outputs = run_vllm(
                requests,
                args.n,
                EngineArgs.from_cli_args(args),
                disable_detokenize=args.disable_detokenize,
                do_profile=args.profile,
            )
    elif args.backend == "hf":
        assert args.tensor_parallel_size == 1
        if args.profile:
            raise NotImplementedError("Profiling not implemented yet for backend='hf'.")
        elapsed_time = run_hf(
            requests,
            args.model,
            tokenizer,
            args.n,
            args.hf_max_batch_size,
            args.trust_remote_code,
            args.disable_detokenize,
            dtype=args.dtype,
            enable_torch_compile=args.hf_enable_torch_compile,
        )
    elif args.backend == "vllm-chat":
        elapsed_time, request_outputs = run_vllm_chat(
            requests,
            args.n,
            EngineArgs.from_cli_args(args),
            disable_detokenize=args.disable_detokenize,
            do_profile=args.profile,
        )
    else:
        raise ValueError(f"Unknown backend: {args.backend}")

    if request_outputs:
        # Note: with the vllm and vllm-chat backends,
        # we have request_outputs, which we use to count tokens.
        total_prompt_tokens = 0
        total_output_tokens = 0
        for ro in request_outputs:
            if not isinstance(ro, RequestOutput):
                continue
            total_prompt_tokens += (
                len(ro.prompt_token_ids) if ro.prompt_token_ids else 0
            )
            total_output_tokens += sum(len(o.token_ids) for o in ro.outputs if o)
        total_num_tokens = total_prompt_tokens + total_output_tokens
    else:
        total_num_tokens = sum(r.prompt_len + r.expected_output_len for r in requests)
        total_output_tokens = sum(r.expected_output_len for r in requests)
        total_prompt_tokens = total_num_tokens - total_output_tokens

    if is_multi_modal and args.backend != "vllm-chat":
        print(
            "\033[91mWARNING\033[0m: Multi-modal request with "
            f"{args.backend} backend detected. The "
            "following metrics are not accurate because image tokens are not"
            " counted. See vllm-project/vllm/issues/9778 for details."
        )
        # TODO(vllm-project/vllm/issues/9778): Count multi-modal token length.
        # vllm-chat backend counts the image tokens now

    print(
        f"Throughput: {len(requests) / elapsed_time:.2f} requests/s, "
        f"{total_num_tokens / elapsed_time:.2f} total tokens/s, "
        f"{total_output_tokens / elapsed_time:.2f} output tokens/s"
    )
    print(f"Total num prompt tokens:  {total_prompt_tokens}")
    print(f"Total num output tokens:  {total_output_tokens}")

    # Output JSON results if specified
    if args.output_json:
        results = {
            "elapsed_time": elapsed_time,
            "num_requests": len(requests),
            "total_num_tokens": total_num_tokens,
            "requests_per_second": len(requests) / elapsed_time,
            "tokens_per_second": total_num_tokens / elapsed_time,
        }
        with open(args.output_json, "w") as f:
            json.dump(results, f, indent=4)
        save_to_pytorch_benchmark_format(args, results)
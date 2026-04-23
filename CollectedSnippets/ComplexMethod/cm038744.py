async def main_async(args: argparse.Namespace) -> dict[str, Any]:
    print(args)
    random.seed(args.seed)
    np.random.seed(args.seed)

    # Validate ramp-up arguments
    if args.ramp_up_strategy is not None:
        if args.request_rate != float("inf"):
            raise ValueError(
                "When using ramp-up, do not specify --request-rate. "
                "The request rate will be controlled by ramp-up parameters. "
                "Please remove the --request-rate argument."
            )
        if args.ramp_up_start_rps is None or args.ramp_up_end_rps is None:
            raise ValueError(
                "When using --ramp-up-strategy, both --ramp-up-start-rps and "
                "--ramp-up-end-rps must be specified"
            )
        if args.ramp_up_start_rps < 0 or args.ramp_up_end_rps < 0:
            raise ValueError("Ramp-up start and end RPS must be non-negative")
        if args.ramp_up_start_rps > args.ramp_up_end_rps:
            raise ValueError("Ramp-up start RPS must be less than end RPS")
        if args.ramp_up_strategy == "exponential" and args.ramp_up_start_rps == 0:
            raise ValueError("For exponential ramp-up, the start RPS cannot be 0.")

    label = args.label

    if args.base_url is not None:
        api_url = f"{args.base_url}{args.endpoint}"
        base_url = f"{args.base_url}"
    else:
        host_port = join_host_port(args.host, args.port)
        api_url = f"http://{host_port}{args.endpoint}"
        base_url = f"http://{host_port}"

    # Headers
    headers = None
    if args.header:
        headers = {}
        for item in args.header:
            if "=" in item:
                kvstring = item.split("=", 1)
                headers[kvstring[0].strip()] = kvstring[1].strip()
            else:
                raise ValueError("Invalid header format. Please use KEY=VALUE format.")

    # SSL context configuration
    ssl_context: ssl.SSLContext | bool | None = None
    if args.insecure:
        # Disable SSL certificate verification
        ssl_context = False
    elif "https://" in base_url:
        # Use default SSL context for HTTPS
        ssl_context = True

    # Fetch model from server if not specified
    if args.model is None:
        print("Model not specified, fetching first model from server...")
        model_name, model_id = await get_first_model_from_server(
            base_url, headers, ssl_context
        )
        print(f"First model name: {model_name}, first model id: {model_id}")
    else:
        model_name = args.served_model_name
        model_id = args.model

    if args.skip_tokenizer_init:
        tokenizer_id = None
        tokenizer_mode = None
        tokenizer = None
    else:
        tokenizer_id = args.tokenizer if args.tokenizer is not None else model_id
        tokenizer_mode = args.tokenizer_mode
        tokenizer = get_tokenizer(
            tokenizer_id,
            tokenizer_mode=tokenizer_mode,
            trust_remote_code=args.trust_remote_code,
        )

    # Validate dataset name/path
    if args.dataset_name is None:
        raise ValueError(
            "Please specify '--dataset-name' and the corresponding "
            "'--dataset-path' if required."
        )

    if (
        args.dataset_name
        in ["random", "random-mm", "random-rerank", "prefix_repetition"]
        and args.dataset_path is not None
    ):
        raise ValueError(
            f"Cannot use '{args.dataset_name}' dataset with --dataset-path. "
            "Please specify the appropriate --dataset-name (e.g., "
            "'sharegpt', 'custom', 'sonnet') for your dataset file: "
            f"{args.dataset_path}"
        )

    # Map general --input-len and --output-len to all dataset-specific arguments
    if args.input_len is not None:
        args.random_input_len = args.input_len
        args.sonnet_input_len = args.input_len

    if args.output_len is not None:
        args.random_output_len = args.output_len
        args.sonnet_output_len = args.output_len
        args.sharegpt_output_len = args.output_len
        args.custom_output_len = args.output_len
        args.hf_output_len = args.output_len
        args.spec_bench_output_len = args.output_len
        args.prefix_repetition_output_len = args.output_len

    # when using random datasets, default to ignoring EOS
    # so generation runs to the requested length
    if (
        args.dataset_name in ("random", "random-mm")
        and args.backend in OPENAI_COMPATIBLE_BACKENDS
    ):
        args.ignore_eos = True

    # Load the dataset.
    input_requests = get_samples(args, tokenizer)
    goodput_config_dict = check_goodput_args(args)

    backend = args.backend
    task_type = TaskType.POOLING if backend in POOLING_BACKENDS else TaskType.GENERATION

    # Collect the sampling parameters.
    if task_type == TaskType.GENERATION:
        sampling_params = {
            k: v
            for k, v in {
                "top_p": args.top_p,
                "top_k": args.top_k,
                "min_p": args.min_p,
                "temperature": args.temperature,
                "frequency_penalty": args.frequency_penalty,
                "presence_penalty": args.presence_penalty,
                "repetition_penalty": args.repetition_penalty,
            }.items()
            if v is not None
        }

        # Sampling parameters are only supported by openai-compatible backend.
        if sampling_params and args.backend not in OPENAI_COMPATIBLE_BACKENDS:
            raise ValueError(
                "Sampling parameters are only supported by openai-compatible backends."
            )

        if "temperature" not in sampling_params:
            print(
                "WARNING: vllm bench serve no longer sets temperature==0 (greedy) "
                "in requests by default. The default will be determined on the "
                "server side and can be model/API specific. "
                "For the old behavior, include --temperature=0."
            )

        default_percentile_metrics = "ttft,tpot,itl"
    else:
        sampling_params = {}
        default_percentile_metrics = "e2el"

    extra_body = args.extra_body or {}
    extra_body = {**sampling_params, **extra_body}

    percentile_metrics: str = args.percentile_metrics or default_percentile_metrics

    # Avoid GC processing "static" data - reduce pause times.
    freeze_gc_heap()

    benchmark_result = await benchmark(
        task_type=task_type,
        endpoint_type=backend,
        api_url=api_url,
        base_url=base_url,
        model_id=model_id,
        model_name=model_name,
        tokenizer=tokenizer,
        input_requests=input_requests,
        logprobs=args.logprobs,
        request_rate=args.request_rate,
        burstiness=args.burstiness,
        disable_tqdm=args.disable_tqdm,
        num_warmups=args.num_warmups,
        profile=args.profile,
        selected_percentile_metrics=percentile_metrics.split(","),
        selected_percentiles=[float(p) for p in args.metric_percentiles.split(",")],
        ignore_eos=args.ignore_eos,
        goodput_config_dict=goodput_config_dict,
        max_concurrency=args.max_concurrency,
        lora_modules=args.lora_modules,
        lora_assignment=args.lora_assignment,
        extra_headers=headers,
        extra_body=extra_body,
        ramp_up_strategy=args.ramp_up_strategy,
        ramp_up_start_rps=args.ramp_up_start_rps,
        ramp_up_end_rps=args.ramp_up_end_rps,
        ready_check_timeout_sec=args.ready_check_timeout_sec,
        ssl_context=ssl_context,
    )

    # Save config and results to json
    result_json: dict[str, Any] = {}

    # Setup
    current_dt = datetime.now().strftime("%Y%m%d-%H%M%S")
    result_json["date"] = current_dt
    result_json["endpoint_type"] = args.backend  # for backward compatibility
    result_json["backend"] = args.backend
    result_json["label"] = label
    result_json["model_id"] = model_id
    result_json["tokenizer_id"] = tokenizer_id
    result_json["num_prompts"] = args.num_prompts

    # Metadata
    if args.metadata:
        for item in args.metadata:
            if "=" in item:
                kvstring = item.split("=", 1)
                result_json[kvstring[0].strip()] = kvstring[1].strip()
            else:
                raise ValueError(
                    "Invalid metadata format. Please use KEY=VALUE format."
                )

    # Traffic
    result_json["request_rate"] = (
        args.request_rate if args.request_rate < float("inf") else "inf"
    )
    result_json["burstiness"] = args.burstiness
    result_json["max_concurrency"] = args.max_concurrency

    if args.ramp_up_strategy is not None:
        result_json["ramp_up_strategy"] = args.ramp_up_strategy
        result_json["ramp_up_start_rps"] = args.ramp_up_start_rps
        result_json["ramp_up_end_rps"] = args.ramp_up_end_rps

    # Merge with benchmark result
    result_json = {**result_json, **benchmark_result}

    # Compute file_name once before using it for plots or saving results
    file_name = compute_result_filename(args, model_id, label, current_dt)

    # Generate timeline plot if requested
    if args.plot_timeline:
        try:
            from vllm.benchmarks.plot import generate_timeline_plot

            # Prepare per-request data for timeline
            per_request_data = []
            start_times = benchmark_result.get("start_times", [])
            ttfts = benchmark_result.get("ttfts", [])
            itls = benchmark_result.get("itls", [])
            input_lens = benchmark_result.get("input_lens", [])
            output_lens = benchmark_result.get("output_lens", [])

            if start_times and ttfts and itls:
                for i in range(len(start_times)):
                    # Calculate latency as ttft + sum of all itls
                    latency = ttfts[i] + sum(itls[i]) if itls[i] else ttfts[i]

                    per_request_data.append(
                        {
                            "start_time": start_times[i],
                            "ttft": ttfts[i],
                            "itl": itls[i],
                            "latency": latency,
                            "prompt_len": input_lens[i],
                            "output_tokens": output_lens[i],
                        }
                    )

                timeline_path = Path(file_name).with_suffix(".timeline.html")
                # Convert thresholds from milliseconds to seconds
                itl_thresholds_sec = [t / 1000.0 for t in args.timeline_itl_thresholds]
                generate_timeline_plot(
                    per_request_data, timeline_path, itl_thresholds=itl_thresholds_sec
                )
            else:
                warnings.warn(
                    "Timeline plot requires detailed metrics. "
                    "Ensure the benchmark completed successfully.",
                    stacklevel=2,
                )
        except Exception as e:
            warnings.warn(f"Failed to generate timeline plot: {e}", stacklevel=2)

    # Generate dataset statistics plot if requested
    if args.plot_dataset_stats:
        try:
            from vllm.benchmarks.plot import generate_dataset_stats_plot

            # Prepare per-request data for dataset stats
            per_request_data = []
            input_lens = benchmark_result.get("input_lens", [])
            output_lens = benchmark_result.get("output_lens", [])

            if input_lens and output_lens:
                for req_input_len, req_output_len in zip(input_lens, output_lens):
                    per_request_data.append(
                        {
                            "prompt_len": req_input_len,
                            "output_tokens": req_output_len,
                        }
                    )

                stats_path = Path(file_name).with_suffix(".dataset_stats.png")
                generate_dataset_stats_plot(per_request_data, stats_path)
            else:
                warnings.warn(
                    "Dataset statistics plot requires input and "
                    "output length data. Ensure the benchmark completed "
                    "successfully.",
                    stacklevel=2,
                )
        except Exception as e:
            warnings.warn(
                f"Failed to generate dataset statistics plot: {e}", stacklevel=2
            )

    if not args.save_detailed:
        # Remove fields with too many data points
        for field in [
            "input_lens",
            "output_lens",
            "start_times",
            "ttfts",
            "itls",
            "generated_texts",
            "errors",
        ]:
            if field in result_json:
                del result_json[field]
            if field in benchmark_result:
                del benchmark_result[field]

    # Save to file
    if args.save_result or args.append_result:
        with open(
            file_name, mode="a+" if args.append_result else "w", encoding="utf-8"
        ) as outfile:
            # Append a newline.
            if args.append_result and outfile.tell() != 0:
                outfile.write("\n")
            json.dump(result_json, outfile)
        save_to_pytorch_benchmark_format(args, result_json, file_name)

    return result_json
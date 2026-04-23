async def benchmark(
    backend: str,
    api_url: str,
    base_url: str,
    model_id: str,
    tokenizer: PreTrainedTokenizerBase,
    input_requests: list[SampleRequest],
    request_rate: float,
    burstiness: float,
    disable_tqdm: bool,
    profile: bool,
    selected_percentile_metrics: list[str],
    selected_percentiles: list[str],
    ignore_eos: bool,
    max_concurrency: int | None,
    structured_output_ratio: float,
    goodput_config_dict: dict[str, float] | None = None,
):
    if backend in ASYNC_REQUEST_FUNCS:
        request_func = ASYNC_REQUEST_FUNCS[backend]
    else:
        raise ValueError(f"Unknown backend: {backend}")

    def prepare_extra_body(request) -> dict:
        extra_body = {}
        # Add the schema to the extra_body
        extra_body["structured_outputs"] = {}
        extra_body["structured_outputs"][request.structure_type] = request.schema
        return extra_body

    print("Starting initial single prompt test run...")
    structured_output_req_idx = random.sample(
        range(len(input_requests)), int(len(input_requests) * structured_output_ratio)
    )

    test_request = input_requests[0]
    test_req_extra_body = (
        prepare_extra_body(test_request) if 0 in structured_output_req_idx else None
    )
    test_input = RequestFuncInput(
        model=model_id,
        prompt=test_request.prompt,
        api_url=api_url,
        prompt_len=test_request.prompt_len,
        output_len=test_request.expected_output_len,
        ignore_eos=ignore_eos,
        extra_body=test_req_extra_body,
    )
    test_output = await request_func(request_func_input=test_input)
    if not test_output.success:
        raise ValueError(
            "Initial test run failed - Please make sure benchmark arguments "
            f"are correctly specified. Error: {test_output.error}"
        )
    else:
        print("Initial test run completed. Starting main benchmark run...")

    if profile:
        print("Starting profiler...")
        profile_input = RequestFuncInput(
            model=model_id,
            prompt=test_request.prompt,
            api_url=base_url + "/start_profile",
            prompt_len=test_request.prompt_len,
            output_len=test_request.expected_output_len,
            ignore_eos=ignore_eos,
            extra_body=test_req_extra_body,
        )
        profile_output = await request_func(request_func_input=profile_input)
        if profile_output.success:
            print("Profiler started")

    distribution = "Poisson process" if burstiness == 1.0 else "Gamma distribution"

    print(f"Traffic request rate: {request_rate}")
    print(f"Burstiness factor: {burstiness} ({distribution})")
    print(f"Maximum request concurrency: {max_concurrency}")

    pbar = None if disable_tqdm else tqdm(total=len(input_requests))

    semaphore = asyncio.Semaphore(max_concurrency) if max_concurrency else nullcontext()

    async def limited_request_func(request_func_input, pbar):
        async with semaphore:
            return await request_func(request_func_input=request_func_input, pbar=pbar)

    benchmark_start_time = time.perf_counter()
    tasks: list[asyncio.Task] = []
    expected: list[str] = []
    async for i, request in get_request(input_requests, request_rate, burstiness):
        extra_body = (
            prepare_extra_body(request) if i in structured_output_req_idx else None
        )
        request_func_input = RequestFuncInput(
            model=model_id,
            prompt=request.prompt,
            api_url=api_url,
            prompt_len=request.prompt_len,
            output_len=request.expected_output_len,
            ignore_eos=ignore_eos,
            extra_body=extra_body,
        )
        expected.append(request.completion)
        tasks.append(
            asyncio.create_task(
                limited_request_func(request_func_input=request_func_input, pbar=pbar)
            )
        )
    outputs: list[RequestFuncOutput] = await asyncio.gather(*tasks)

    if pbar is not None:
        pbar.close()

    benchmark_duration = time.perf_counter() - benchmark_start_time

    metrics, actual_output_lens = calculate_metrics(
        input_requests=input_requests,
        outputs=outputs,
        dur_s=benchmark_duration,
        tokenizer=tokenizer,
        selected_percentile_metrics=selected_percentile_metrics,
        selected_percentiles=selected_percentiles,
        goodput_config_dict=goodput_config_dict,
    )

    print("{s:{c}^{n}}".format(s=" Serving Benchmark Result ", n=50, c="="))
    print("{:<40} {:<10}".format("Successful requests:", metrics.completed))
    if max_concurrency is not None:
        print("{:<40} {:<10}".format("Maximum request concurrency:", max_concurrency))
    if request_rate != float("inf"):
        print("{:<40} {:<10.2f}".format("Request rate configured (RPS):", request_rate))
    print("{:<40} {:<10.2f}".format("Benchmark duration (s):", benchmark_duration))
    print("{:<40} {:<10}".format("Total input tokens:", metrics.total_input))
    print("{:<40} {:<10}".format("Total generated tokens:", metrics.total_output))
    print(
        "{:<40} {:<10.2f}".format(
            "Request throughput (req/s):", metrics.request_throughput
        )
    )
    if goodput_config_dict:
        print(
            "{:<40} {:<10.2f}".format(
                "Request goodput (req/s):", metrics.request_goodput
            )
        )
    print(
        "{:<40} {:<10.2f}".format(
            "Output token throughput (tok/s):", metrics.output_throughput
        )
    )
    print(
        "{:<40} {:<10.2f}".format(
            "Total token throughput (tok/s):", metrics.total_token_throughput
        )
    )

    result = {
        "duration": benchmark_duration,
        "completed": metrics.completed,
        "total_input_tokens": metrics.total_input,
        "total_output_tokens": metrics.total_output,
        "request_throughput": metrics.request_throughput,
        "output_throughput": metrics.output_throughput,
        "total_token_throughput": metrics.total_token_throughput,
        "ttft_description": pd.Series([output.ttft for output in outputs])
        .describe()
        .to_dict(),
        "tpot_description": pd.Series([output.tpot for output in outputs])
        .describe()
        .to_dict(),
        "input_lens": [output.prompt_len for output in outputs],
        "output_lens": actual_output_lens,
        "ttfts": [output.ttft for output in outputs],
        "itls": [output.itl for output in outputs],
        "errors": [output.error for output in outputs],
    }

    ret = [
        {"generated": output.generated_text, "expected": gt}
        for output, gt in zip(outputs, expected)
    ]

    def process_one_metric(
        # E.g., "ttft"
        metric_attribute_name: str,
        # E.g., "TTFT"
        metric_name: str,
        # E.g., "Time to First Token"
        metric_header: str,
    ):
        # This function prints and adds statistics of the specified
        # metric.
        if metric_attribute_name not in selected_percentile_metrics:
            return
        print("{s:{c}^{n}}".format(s=metric_header, n=50, c="-"))
        print(
            "{:<40} {:<10.2f}".format(
                f"Mean {metric_name} (ms):",
                getattr(metrics, f"mean_{metric_attribute_name}_ms"),
            )
        )
        print(
            "{:<40} {:<10.2f}".format(
                f"Median {metric_name} (ms):",
                getattr(metrics, f"median_{metric_attribute_name}_ms"),
            )
        )
        result[f"mean_{metric_attribute_name}_ms"] = getattr(
            metrics, f"mean_{metric_attribute_name}_ms"
        )
        result[f"median_{metric_attribute_name}_ms"] = getattr(
            metrics, f"median_{metric_attribute_name}_ms"
        )
        result[f"std_{metric_attribute_name}_ms"] = getattr(
            metrics, f"std_{metric_attribute_name}_ms"
        )
        for p, value in getattr(metrics, f"percentiles_{metric_attribute_name}_ms"):
            p_word = str(int(p)) if int(p) == p else str(p)
            print("{:<40} {:<10.2f}".format(f"P{p_word} {metric_name} (ms):", value))
            result[f"p{p_word}_{metric_attribute_name}_ms"] = value

    process_one_metric("ttft", "TTFT", "Time to First Token")
    process_one_metric("tpot", "TPOT", "Time per Output Token (excl. 1st token)")
    process_one_metric("itl", "ITL", "Inter-token Latency")
    process_one_metric("e2el", "E2EL", "End-to-end Latency")

    print("=" * 50)

    if profile:
        print("Stopping profiler...")
        profile_input = RequestFuncInput(
            model=model_id,
            prompt=test_request.prompt,
            api_url=base_url + "/stop_profile",
            prompt_len=test_request.prompt_len,
            output_len=test_request.expected_output_len,
            extra_body={test_request.structure_type: test_request.schema},
        )
        profile_output = await request_func(request_func_input=profile_input)
        if profile_output.success:
            print("Profiler stopped")

    return result, ret
def calculate_metrics(
    input_requests: list[SampleRequest],
    outputs: list[RequestFuncOutput],
    dur_s: float,
    tokenizer: TokenizerLike,
    selected_percentiles: list[float],
    goodput_config_dict: dict[str, float],
) -> tuple[BenchmarkMetrics, list[int]]:
    """Calculate the metrics for the benchmark.

    Args:
        input_requests: The input requests.
        outputs: The outputs of the requests.
        dur_s: The duration of the benchmark.
        tokenizer: The tokenizer to use.
        selected_percentiles: The percentiles to select.
        goodput_config_dict: The goodput configuration.

    Returns:
        A tuple of the benchmark metrics and the actual output lengths.
    """
    actual_output_lens: list[int] = []
    total_input = 0
    completed = 0
    good_completed = 0
    itls: list[float] = []
    tpots: list[float] = []
    all_tpots: list[float] = []
    ttfts: list[float] = []
    e2els: list[float] = []
    input_audio_duration = 0.0
    for i in range(len(outputs)):
        if outputs[i].success:
            output_len = outputs[i].output_tokens

            if not output_len:
                if tokenizer is None:
                    output_len = 1
                else:
                    # We use the tokenizer to count the number of output tokens
                    # for some serving backends instead of looking at
                    # len(outputs[i].itl) since multiple output tokens may be
                    # bundled together
                    # Note : this may inflate the output token count slightly
                    output_len = len(
                        tokenizer(
                            outputs[i].generated_text, add_special_tokens=False
                        ).input_ids
                    )
            actual_output_lens.append(output_len)
            total_input += outputs[i].prompt_len
            tpot = 0
            if output_len > 1:
                latency_minus_ttft = outputs[i].latency - outputs[i].ttft
                tpot = latency_minus_ttft / (output_len - 1)
                tpots.append(tpot)
            # Note: if output_len <= 1, we regard tpot as 0 for goodput
            all_tpots.append(tpot)
            itls += outputs[i].itl
            ttfts.append(outputs[i].ttft)
            e2els.append(outputs[i].latency)
            input_audio_duration += outputs[i].input_audio_duration
            completed += 1
        else:
            actual_output_lens.append(0)

    if goodput_config_dict:
        valid_metrics = []
        slo_values = []

        if "ttft" in goodput_config_dict:
            valid_metrics.append(ttfts)
            slo_values.append(
                goodput_config_dict["ttft"] / MILLISECONDS_TO_SECONDS_CONVERSION
            )
        if "tpot" in goodput_config_dict:
            valid_metrics.append(all_tpots)
            slo_values.append(
                goodput_config_dict["tpot"] / MILLISECONDS_TO_SECONDS_CONVERSION
            )
        if "e2el" in goodput_config_dict:
            valid_metrics.append(e2els)
            slo_values.append(
                goodput_config_dict["e2el"] / MILLISECONDS_TO_SECONDS_CONVERSION
            )

        for req_metric in zip(*valid_metrics):
            is_good_req = all([s >= r for s, r in zip(slo_values, req_metric)])
            if is_good_req:
                good_completed += 1

    if completed == 0:
        warnings.warn(
            "All requests failed. This is likely due to a misconfiguration "
            "on the benchmark arguments.",
            stacklevel=2,
        )

    # Calculate max output tokens per second metric
    max_output_tokens_per_s = 0.0
    max_concurrent_requests = 0

    # Find the time range across all successful requests
    successful_outputs = [output for output in outputs if output.success]
    failed_outputs = [output for output in outputs if not output.success]

    if len(failed_outputs) > 0:
        print("Failed requests during benchmark run detected (capping to 10):")
        for i, err in enumerate(failed_outputs[:10]):
            print(f"Error {i}: {err.error}")

    if successful_outputs:
        min_start_time = min(output.start_time for output in successful_outputs)
        max_end_time = max(
            output.start_time + output.latency for output in successful_outputs
        )

        # Create second buckets (ceiling to ensure we capture all time)
        duration_seconds = int(np.ceil(max_end_time - min_start_time)) + 1
        tokens_per_second = np.zeros(duration_seconds)
        concurrent_requests_per_second = np.zeros(duration_seconds)

        for i, output in enumerate(successful_outputs):
            # Calculate token generation timestamp using
            # start_time, ttft, and itl
            token_times = [output.start_time + output.ttft]
            current_time = token_times[0]
            for itl_value in output.itl:
                current_time += itl_value
                token_times.append(current_time)

            # Add tokens to second buckets
            for token_time in token_times:
                second_bucket = int(token_time - min_start_time)
                if 0 <= second_bucket < duration_seconds:
                    tokens_per_second[second_bucket] += 1

            # Track concurrent requests for each second this request was active
            request_start_second = int(output.start_time - min_start_time)
            request_end_second = int(
                (output.start_time + output.latency) - min_start_time
            )

            for second in range(request_start_second, request_end_second + 1):
                concurrent_requests_per_second[second] += 1

        # Find the maximum tokens per second and corresponding
        # concurrent requests
        if len(tokens_per_second) > 0:
            max_output_tokens_per_s = float(np.max(tokens_per_second))
            max_concurrent_requests = int(np.max(concurrent_requests_per_second))

        if TERM_PLOTLIB_AVAILABLE:
            import termplotlib as tpl

            fig = tpl.figure()
            fig.plot(
                np.arange(len(tokens_per_second)),
                tokens_per_second,
                title="Output tokens per second",
            )
            fig.plot(
                np.arange(len(concurrent_requests_per_second)),
                concurrent_requests_per_second,
                title="Concurrent requests per second",
            )
            fig.show()
        else:
            print("tip: install termplotlib and gnuplot to plot the metrics")

    metrics = BenchmarkMetrics(
        completed=completed,
        failed=len(failed_outputs),
        total_input=total_input,
        total_output=sum(actual_output_lens),
        request_throughput=completed / dur_s,
        request_goodput=good_completed / dur_s,
        output_throughput=sum(actual_output_lens) / dur_s,
        total_token_throughput=(total_input + sum(actual_output_lens)) / dur_s,
        mean_ttft_ms=np.mean(ttfts or 0)
        * 1000,  # ttfts is empty if streaming is not supported by the endpoint
        std_ttft_ms=np.std(ttfts or 0) * 1000,
        median_ttft_ms=np.median(ttfts or 0) * 1000,
        percentiles_ttft_ms=[
            (p, np.percentile(ttfts or 0, p) * 1000) for p in selected_percentiles
        ],
        mean_tpot_ms=np.mean(tpots or 0) * 1000,
        std_tpot_ms=np.std(tpots or 0) * 1000,
        median_tpot_ms=np.median(tpots or 0) * 1000,
        percentiles_tpot_ms=[
            (p, np.percentile(tpots or 0, p) * 1000) for p in selected_percentiles
        ],
        mean_itl_ms=np.mean(itls or 0) * 1000,
        std_itl_ms=np.std(itls or 0) * 1000,
        median_itl_ms=np.median(itls or 0) * 1000,
        percentiles_itl_ms=[
            (p, np.percentile(itls or 0, p) * 1000) for p in selected_percentiles
        ],
        mean_e2el_ms=np.mean(e2els or 0) * 1000,
        std_e2el_ms=np.std(e2els or 0) * 1000,
        median_e2el_ms=np.median(e2els or 0) * 1000,
        percentiles_e2el_ms=[
            (p, np.percentile(e2els or 0, p) * 1000) for p in selected_percentiles
        ],
        max_output_tokens_per_s=max_output_tokens_per_s,
        max_concurrent_requests=max_concurrent_requests,
        rtfx=input_audio_duration / dur_s,
    )

    return metrics, actual_output_lens
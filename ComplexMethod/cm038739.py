async def get_request(
    input_requests: list[SampleRequest],
    request_rate: float,
    burstiness: float = 1.0,
    ramp_up_strategy: Literal["linear", "exponential"] | None = None,
    ramp_up_start_rps: int | None = None,
    ramp_up_end_rps: int | None = None,
) -> AsyncGenerator[tuple[SampleRequest, float], None]:
    """
    Asynchronously generates requests at a specified rate
    with OPTIONAL burstiness and OPTIONAL ramp-up strategy.

    Args:
        input_requests:
            A list of input requests, each represented as a SampleRequest.
        request_rate:
            The rate at which requests are generated (requests/s).
        burstiness (optional):
            The burstiness factor of the request generation.
            Only takes effect when request_rate is not inf.
            Default value is 1, which follows a Poisson process.
            Otherwise, the request intervals follow a gamma distribution.
            A lower burstiness value (0 < burstiness < 1) results
            in more bursty requests, while a higher burstiness value
            (burstiness > 1) results in a more uniform arrival of requests.
        ramp_up_strategy (optional):
            The ramp-up strategy. Can be "linear" or "exponential".
            If None, uses constant request rate (specified by request_rate).
        ramp_up_start_rps (optional):
            The starting request rate for ramp-up.
        ramp_up_end_rps (optional):
            The ending request rate for ramp-up.
    """
    assert burstiness > 0, (
        f"A positive burstiness factor is expected, but given {burstiness}."
    )
    # Convert to list to get length for ramp-up calculations
    if isinstance(input_requests, Iterable) and not isinstance(input_requests, list):
        input_requests = list(input_requests)

    total_requests = len(input_requests)
    assert total_requests > 0, "No requests provided."

    # Precompute delays among requests to minimize request send laggings
    request_rates = []
    delay_ts = []
    for request_index, request in enumerate(input_requests):
        current_request_rate = _get_current_request_rate(
            ramp_up_strategy,
            ramp_up_start_rps,
            ramp_up_end_rps,
            request_index,
            total_requests,
            request_rate,
        )
        assert current_request_rate > 0.0, (
            f"Obtained non-positive request rate {current_request_rate}."
        )
        request_rates.append(current_request_rate)
        if current_request_rate == float("inf"):
            delay_ts.append(0)
        elif burstiness == float("inf"):
            # when burstiness tends to infinity, the delay time becomes constant
            # and tends to the inverse of the request rate
            delay_ts.append(1.0 / current_request_rate)
        else:
            theta = 1.0 / (current_request_rate * burstiness)

            # Sample the request interval from the gamma distribution.
            # If burstiness is 1, it follows exponential distribution.
            delay_ts.append(np.random.gamma(shape=burstiness, scale=theta))

    # Calculate the cumulative delay time from the first sent out requests.
    for i in range(1, len(delay_ts)):
        delay_ts[i] += delay_ts[i - 1]
    if ramp_up_strategy is None and delay_ts[-1] != 0:
        # When ramp_up_strategy is not set, we assume the request rate is fixed
        # and all requests should be sent in target_total_delay_s, the following
        # logic would re-scale delay time to ensure the final delay_ts
        # align with target_total_delay_s.
        #
        # NOTE: If we simply accumulate the random delta values
        # from the gamma distribution, their sum would have 1-2% gap
        # from target_total_delay_s. The purpose of the following logic is to
        # close the gap for stabilizing the throughput data
        # from different random seeds.
        target_total_delay_s = total_requests / request_rate
        normalize_factor = target_total_delay_s / delay_ts[-1]
        delay_ts = [delay * normalize_factor for delay in delay_ts]

    start_ts = time.time()
    for request_index, request in enumerate(input_requests):
        if delay_ts[request_index] > 0:
            current_ts = time.time()
            sleep_interval_s = start_ts + delay_ts[request_index] - current_ts
            if sleep_interval_s > 0:
                await asyncio.sleep(sleep_interval_s)
        yield request, request_rates[request_index]
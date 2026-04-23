async def send_request(
    session: aiohttp.ClientSession,
    messages: list[dict[str, str]],
    chat_url: str,
    model: str,
    stream: bool = True,
    min_tokens: int | None = None,
    max_tokens: int | None = None,
    timeout_sec: int = 120,
) -> ServerResponse:
    payload = {
        "model": model,
        "messages": messages,
        "seed": 0,
        "temperature": 0.0,
    }

    if stream:
        payload["stream"] = True
        payload["stream_options"] = {"include_usage": False}

    if min_tokens is not None:
        payload["min_tokens"] = min_tokens

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    headers = {"Content-Type": "application/json"}

    # Calculate the timeout for the request
    if max_tokens is not None:
        # Assume TPOT of 200ms and use max_tokens to determine timeout
        token_based_timeout = int(max_tokens * 0.2)
        if token_based_timeout > timeout_sec:
            timeout_sec = token_based_timeout
            logger.info(
                "Using timeout of %ds based on max_tokens %d",
                timeout_sec,
                max_tokens,
            )
    timeout = aiohttp.ClientTimeout(total=timeout_sec)

    valid_response = True
    ttft: float | None = None
    chunk_delay: list[int] = []
    latency: float | None = None
    first_chunk = ""
    generated_text = ""

    start_time: int = time.perf_counter_ns()
    most_recent_timestamp: int = start_time

    async with session.post(
        url=chat_url, json=payload, headers=headers, timeout=timeout
    ) as response:
        http_status = HTTPStatus(response.status)
        if http_status == HTTPStatus.OK:
            async for chunk_bytes in response.content:
                chunk_bytes = chunk_bytes.strip()
                if not chunk_bytes:
                    continue

                chunk = chunk_bytes.decode("utf-8").removeprefix("data: ")
                if chunk == "[DONE]":
                    # End of stream
                    latency = time.perf_counter_ns() - start_time
                elif stream is False:
                    data = json.loads(chunk)
                    message = data["choices"][0]["message"]
                    assert message["role"] == "assistant"
                    generated_text += message["content"]
                else:
                    timestamp: int = time.perf_counter_ns()
                    data = json.loads(chunk)

                    # Delta is the new content/text/data
                    delta = data["choices"][0]["delta"]
                    if delta.get("content", None):
                        if ttft is None:
                            # First token
                            first_token_time = time.perf_counter_ns()
                            ttft = first_token_time - start_time
                            first_chunk = delta["content"]
                        else:
                            # Decoding phase
                            chunk_delay.append(timestamp - most_recent_timestamp)

                        generated_text += delta["content"]

                    most_recent_timestamp = timestamp
        else:
            valid_response = False
            content = await response.text()
            logger.warning(
                f"{Color.YELLOW}Received HTTP status {http_status.value} "
                f"({http_status.phrase}): {content}{Color.RESET}"
            )

    if latency is None:
        latency = -1.0
        if valid_response:
            # Streaming is disabled, latency was not set
            latency = time.perf_counter_ns() - start_time

    if ttft is None:
        # The response was a single chunk
        ttft = latency

    # Each chunk may include more than one token
    tpot: float = mean(chunk_delay) if len(chunk_delay) > 0 else 0.0
    num_chunks: int = len(chunk_delay)

    sr = ServerResponse(
        valid=valid_response,
        ttft_ms=nanosec_to_millisec(ttft) if ttft > 0.0 else -1.0,
        tpot_ms=nanosec_to_millisec(tpot),
        latency_ms=nanosec_to_millisec(latency),
        start_time_ms=nanosec_to_millisec(start_time),
        first_chunk=first_chunk,
        content=generated_text,
        num_chunks=num_chunks,
    )
    return sr
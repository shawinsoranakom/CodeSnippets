async def test_completion_streaming(
    client: openai.AsyncOpenAI, server: RemoteOpenAIServer, model_name: str
) -> None:
    prompt = "What is an LLM?"

    async def make_streaming_request():
        # Perform a non-streaming request to get the expected full output
        single_completion = await client.completions.create(
            model=model_name,
            prompt=prompt,
            max_tokens=5,
            temperature=0.0,
        )
        single_output = single_completion.choices[0].text

        # Perform the streaming request
        stream = await client.completions.create(
            model=model_name, prompt=prompt, max_tokens=5, temperature=0.0, stream=True
        )
        chunks: list[str] = []
        finish_reason_count = 0
        last_chunk = None
        async for chunk in stream:
            chunks.append(chunk.choices[0].text)
            if chunk.choices[0].finish_reason is not None:
                finish_reason_count += 1
            last_chunk = chunk  # Keep track of the last chunk

        # finish reason should only return in the last block for OpenAI API
        assert finish_reason_count == 1, "Finish reason should appear exactly once."
        assert last_chunk is not None, "Stream should have yielded at least one chunk."
        assert last_chunk.choices[0].finish_reason == "length", (
            "Finish reason should be 'length'."
        )
        # Check that the combined text matches the non-streamed version.
        assert "".join(chunks) == single_output, (
            "Streamed output should match non-streamed output."
        )
        return True  # Indicate success for this request

    # Test single request
    result = await make_streaming_request()
    assert result is not None

    await asyncio.sleep(0.5)

    # Send two bursts of requests
    num_requests = 100
    tasks = [make_streaming_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)

    assert len(results) == num_requests, (
        f"Expected {num_requests} results, got {len(results)}"
    )
    assert all(results), "Not all streaming requests completed successfully."

    await asyncio.sleep(0.5)

    tasks = [make_streaming_request() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)

    assert len(results) == num_requests, (
        f"Expected {num_requests} results, got {len(results)}"
    )
    assert all(results), "Not all streaming requests completed successfully."

    # Check request balancing via Prometheus metrics if DP_SIZE > 1
    check_request_balancing(server, int(DP_SIZE))
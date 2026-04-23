async def fetch_spec_decode_metrics(
    base_url: str, session: aiohttp.ClientSession
) -> SpecDecodeMetrics | None:
    """Fetch speculative decoding metrics from the server's Prometheus endpoint.

    Returns None if speculative decoding is not enabled or metrics are not available.
    """
    metrics_url = f"{base_url}/metrics"
    try:
        async with session.get(metrics_url) as response:
            if response.status != 200:
                return None
            text = await response.text()

            num_drafts = 0
            num_draft_tokens = 0
            num_accepted_tokens = 0
            accepted_per_pos: dict[int, int] = {}
            found_spec_decode = False

            for line in text.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                if line.startswith("vllm:spec_decode"):
                    found_spec_decode = True
                    parts = line.split()
                    if parts:
                        with contextlib.suppress(ValueError):
                            if "num_drafts" in line:
                                num_drafts += int(float(parts[-1]))
                            elif "num_draft_tokens" in line:
                                num_draft_tokens += int(float(parts[-1]))
                            elif "num_accepted_tokens_per_pos" in line:
                                pos_label = 'position="'
                                if pos_label in line:
                                    start = line.index(pos_label) + len(pos_label)
                                    end = line.index('"', start)
                                    pos = int(line[start:end])
                                    val = int(float(parts[-1]))
                                    accepted_per_pos[pos] = (
                                        accepted_per_pos.get(pos, 0) + val
                                    )
                            elif "num_accepted_tokens" in line:
                                num_accepted_tokens += int(float(parts[-1]))

            if not found_spec_decode:
                return None

            return SpecDecodeMetrics(
                num_drafts=num_drafts,
                num_draft_tokens=num_draft_tokens,
                num_accepted_tokens=num_accepted_tokens,
                accepted_per_pos=accepted_per_pos,
            )
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return None
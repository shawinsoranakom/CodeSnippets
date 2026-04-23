async def fanout_encoder_primer(
    orig_request: dict,
    e_urls: list[str],
    req_id: str,
) -> None:
    """
    1. Build one request *per MM item* with all text removed.
    2. Send them concurrently to the encode cluster.
    3. Raise if any of them fails.
    """
    logger.info("[%s] Processing multimodal items...", req_id)

    mm_items = extract_mm_items(orig_request)
    if not mm_items:
        logger.info("[%s] No multimodal items, skipping encoder", req_id)
        return  # nothing to do

    logger.info("[%s] got %d multimodal items...", req_id, len(mm_items))

    tasks = []

    # Round-robin over encode servers to distribute load a bit
    url_cycle = (e_urls[i % len(e_urls)] for i in range(len(mm_items)))

    for idx, (item, target_url) in enumerate(zip(mm_items, url_cycle)):
        # Derive a *child* request id:  <parent>:<index>:<random-short>
        child_req_id = f"{req_id}:{idx}:{uuid.uuid4().hex[:6]}"
        headers = {"x-request-id": child_req_id}

        encoder_req = {
            # You *may* need to keep additional fields
            "model": orig_request.get("model"),
            "messages": [
                {"role": "user", "content": [item]},
            ],
            # Only need 1 token so the server actually runs the encoder path
            "max_tokens": 1,
            "stream": False,
        }
        tasks.append(
            encode_session.post(
                f"{target_url}/v1/chat/completions",
                json=encoder_req,
                headers=headers,
            )
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Fail fast if any sub-request failed
    for idx, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(
                "[%s] Encoder request #%d raised exception: %s",
                req_id,
                idx,
                r,
                exc_info=r,
            )
            raise HTTPException(
                status_code=502, detail=f"Encoder request failed: {str(r)}"
            )
        if r.status != 200:
            try:
                detail = await r.text()
            except Exception:
                detail = "<unable to read body>"
            logger.error(
                "[%s] Encoder request #%d returned status %s: %s",
                req_id,
                idx,
                r.status,
                detail,
            )
            raise HTTPException(
                status_code=r.status,
                detail=f"Encoder request failed: {detail}",
            )

    logger.info(
        "[%s] All %d encoder requests completed successfully", req_id, len(mm_items)
    )
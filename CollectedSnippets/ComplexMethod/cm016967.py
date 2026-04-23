async def _stream_sonilo_music(
    cls: type[IO.ComfyNode],
    endpoint: ApiEndpoint,
    form: aiohttp.FormData,
) -> bytes:
    """POST ``form`` to Sonilo, read the NDJSON stream, and return the first stream's audio bytes."""
    url = urljoin(default_base_url().rstrip("/") + "/", endpoint.path.lstrip("/"))

    headers: dict[str, str] = {}
    headers.update(get_auth_header(cls))
    headers.update(endpoint.headers)

    node_id = get_node_id(cls)
    start_ts = time.monotonic()
    last_chunk_status_ts = 0.0
    audio_streams: dict[int, list[bytes]] = {}
    title: str | None = None

    timeout = aiohttp.ClientTimeout(total=1200.0, sock_read=300.0)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        PromptServer.instance.send_progress_text("Status: Queued", node_id)
        async with session.post(url, data=form, headers=headers) as resp:
            if resp.status >= 400:
                msg = await _extract_error_message(resp)
                raise Exception(f"Sonilo API error ({resp.status}): {msg}")

            while True:
                if is_processing_interrupted():
                    raise ProcessingInterrupted("Task cancelled")

                raw_line = await resp.content.readline()
                if not raw_line:
                    break

                line = raw_line.decode("utf-8").strip()
                if not line:
                    continue

                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning("Sonilo: skipping malformed NDJSON line")
                    continue

                evt_type = evt.get("type")
                if evt_type == "error":
                    code = evt.get("code", "UNKNOWN")
                    message = evt.get("message", "Unknown error")
                    raise Exception(f"Sonilo generation error ({code}): {message}")
                if evt_type == "duration":
                    duration_sec = evt.get("duration_sec")
                    if duration_sec is not None:
                        PromptServer.instance.send_progress_text(
                            f"Status: Generating\nVideo duration: {duration_sec:.1f}s",
                            node_id,
                        )
                elif evt_type in ("titles", "title"):
                    # v2m sends a "titles" list, t2m sends a scalar "title"
                    if evt_type == "titles":
                        titles = evt.get("titles", [])
                        if titles:
                            title = titles[0]
                    else:
                        title = evt.get("title") or title
                    if title:
                        PromptServer.instance.send_progress_text(
                            f"Status: Generating\nTitle: {title}",
                            node_id,
                        )
                elif evt_type == "audio_chunk":
                    stream_idx = evt.get("stream_index", 0)
                    chunk_data = base64.b64decode(evt["data"])

                    if stream_idx not in audio_streams:
                        audio_streams[stream_idx] = []
                    audio_streams[stream_idx].append(chunk_data)

                    now = time.monotonic()
                    if now - last_chunk_status_ts >= 1.0:
                        total_chunks = sum(len(chunks) for chunks in audio_streams.values())
                        elapsed = int(now - start_ts)
                        status_lines = ["Status: Receiving audio"]
                        if title:
                            status_lines.append(f"Title: {title}")
                        status_lines.append(f"Chunks received: {total_chunks}")
                        status_lines.append(f"Time elapsed: {elapsed}s")
                        PromptServer.instance.send_progress_text("\n".join(status_lines), node_id)
                        last_chunk_status_ts = now
                elif evt_type == "complete":
                    break

    if not audio_streams:
        raise Exception("Sonilo API returned no audio data.")

    PromptServer.instance.send_progress_text("Status: Completed", node_id)
    selected_stream = 0 if 0 in audio_streams else min(audio_streams)
    return b"".join(audio_streams[selected_stream])
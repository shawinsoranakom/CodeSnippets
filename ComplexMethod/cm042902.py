async def _run(api: str, urls: int, concurrent: int, chunk: int, stream: bool, report: pathlib.Path):
    client = httpx.AsyncClient(base_url=api, timeout=REQUEST_TIMEOUT, limits=httpx.Limits(max_connections=concurrent+5))
    await _check_health(client)

    url_list = [f"https://httpbin.org/anything/{uuid.uuid4()}" for _ in range(urls)]
    chunks = [url_list[i:i+chunk] for i in range(0, len(url_list), chunk)]
    sem = asyncio.Semaphore(concurrent)

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Batch", style="dim", width=6)
    table.add_column("Success/Fail", width=12)
    table.add_column("Mem", width=14)
    table.add_column("Time (s)")

    agg_success = agg_fail = 0
    deltas, peaks = [], []

    start = time.perf_counter()
    tasks = [asyncio.create_task(_fetch_chunk(client, c, stream, sem)) for c in chunks]
    for idx, coro in enumerate(asyncio.as_completed(tasks), 1):
        res = await coro
        agg_success += res["success_urls"]
        agg_fail += res["failed_urls"]
        if res["mem_metric"] is not None:
            deltas.append(res["mem_metric"])
        if res["peak"] is not None:
            peaks.append(res["peak"])

        mem_txt = f"{res['mem_metric']:.1f}" if res["mem_metric"] is not None else "‑"
        if res["peak"] is not None:
            mem_txt = f"{res['peak']:.1f}/{mem_txt}"

        table.add_row(str(idx), f"{res['success_urls']}/{res['failed_urls']}", mem_txt, f"{res['elapsed']:.2f}")

    console.print(table)
    total_time = time.perf_counter() - start

    summary = {
        "urls": urls,
        "concurrent": concurrent,
        "chunk": chunk,
        "stream": stream,
        "success_urls": agg_success,
        "failed_urls": agg_fail,
        "elapsed_sec": round(total_time, 2),
        "avg_mem": round(statistics.mean(deltas), 2) if deltas else None,
        "max_mem": max(deltas) if deltas else None,
        "avg_peak": round(statistics.mean(peaks), 2) if peaks else None,
        "max_peak": max(peaks) if peaks else None,
    }
    console.print("\n[bold green]Done:[/]" , summary)

    report.mkdir(parents=True, exist_ok=True)
    path = report / f"api_test_{int(time.time())}.json"
    path.write_text(json.dumps(summary, indent=2))
    console.print(f"[green]Summary → {path}")

    await client.aclose()
async def main() -> None:
    args = parse_args()

    urls = make_fake_urls(args.urls)
    batches = [urls[i : i + args.chunk_size] for i in range(0, len(urls), args.chunk_size)]
    endpoint = "/crawl/stream" if args.stream else "/crawl"
    sem = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(base_url=args.base_url, http2=args.http2, timeout=None) as client:
        with Progress(
            "[progress.description]{task.description}",
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            TimeRemainingColumn(),
        ) as progress:
            task_id = progress.add_task("[cyan]bombarding…", total=len(batches))
            tasks = []
            for chunk in batches:
                payload = {
                    "urls": chunk,
                    "browser_config": {"type": "BrowserConfig", "params": {"headless": args.headless}},
                    "crawler_config": {"type": "CrawlerRunConfig", "params": {"cache_mode": "BYPASS", "stream": args.stream}},
                }
                tasks.append(asyncio.create_task(fire(client, endpoint, payload, sem)))
                progress.advance(task_id)

            results = await asyncio.gather(*tasks)

    ok_latencies = [dt for ok, dt in results if ok]
    err_count = sum(1 for ok, _ in results if not ok)

    table = Table(title="Docker API Stress‑Test Summary")
    table.add_column("total", justify="right")
    table.add_column("errors", justify="right")
    table.add_column("p50", justify="right")
    table.add_column("p95", justify="right")
    table.add_column("max", justify="right")

    table.add_row(
        str(len(results)),
        str(err_count),
        pct(ok_latencies, 50),
        pct(ok_latencies, 95),
        f"{max(ok_latencies):.2f}s" if ok_latencies else "-",
    )
    console.print(table)
async def run_full_test(args):
    """Runs the full API stress test process."""
    client = httpx.AsyncClient(base_url=args.api_url, timeout=REQUEST_TIMEOUT)

    if not await check_server_health(client):
        console.print("[bold red]Aborting test due to server health check failure.[/]")
        await client.aclose()
        return
    await client.aclose()

    test = ApiStressTest(
        api_url=args.api_url,
        url_count=args.urls,
        max_concurrent_requests=args.max_concurrent_requests,
        chunk_size=args.chunk_size,
        report_path=args.report_path,
        stream_mode=args.stream,
    )
    results = {}
    try:
        results = await test.run()
    finally:
        await test.close_client()

    if not results:
        console.print("[bold red]Test did not produce results.[/bold red]")
        return

    console.print("\n" + "=" * 80)
    console.print("[bold green]API Stress Test Completed[/bold green]")
    console.print("=" * 80)

    success_rate_reqs = results["successful_requests"] / results["total_api_calls"] * 100 if results["total_api_calls"] > 0 else 0
    success_rate_urls = results["successful_urls"] / results["url_count"] * 100 if results["url_count"] > 0 else 0
    urls_per_second = results["total_urls_processed"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0
    reqs_per_second = results["total_api_calls"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0


    console.print(f"[bold cyan]Test ID:[/bold cyan] {results['test_id']}")
    console.print(f"[bold cyan]Target API:[/bold cyan] {results['api_url']}")
    console.print(f"[bold cyan]Configuration:[/bold cyan] {results['url_count']} URLs, {results['max_concurrent_requests']} concurrent client requests, URLs/Req: {results['chunk_size']}, Stream: {results['stream_mode']}")
    console.print(f"[bold cyan]API Requests:[/bold cyan] {results['successful_requests']} successful, {results['failed_requests']} failed ({results['total_api_calls']} total, {success_rate_reqs:.1f}% success)")
    console.print(f"[bold cyan]URL Processing:[/bold cyan] {results['successful_urls']} successful, {results['failed_urls']} failed ({results['total_urls_processed']} processed, {success_rate_urls:.1f}% success)")
    console.print(f"[bold cyan]Performance:[/bold cyan] {results['total_time_seconds']:.2f}s total | Avg Reqs/sec: {reqs_per_second:.2f} | Avg URLs/sec: {urls_per_second:.2f}")

    # Report Server Memory
    mem_metrics = results.get("server_memory_metrics", {})
    mem_samples = mem_metrics.get("samples", [])
    if mem_samples:
         num_samples = len(mem_samples)
         if results['stream_mode']:
             avg_mem = mem_metrics.get("stream_mode_avg_max_snapshot_mb")
             max_mem = mem_metrics.get("stream_mode_max_max_snapshot_mb")
             avg_str = f"{avg_mem:.1f}" if avg_mem is not None else "N/A"
             max_str = f"{max_mem:.1f}" if max_mem is not None else "N/A"
             console.print(f"[bold cyan]Server Memory (Stream):[/bold cyan] Avg Max Snapshot: {avg_str} MB | Max Max Snapshot: {max_str} MB (across {num_samples} requests)")
         else: # Batch mode
             avg_delta = mem_metrics.get("batch_mode_avg_delta_mb")
             max_delta = mem_metrics.get("batch_mode_max_delta_mb")
             avg_peak = mem_metrics.get("batch_mode_avg_peak_mb")
             max_peak = mem_metrics.get("batch_mode_max_peak_mb")

             avg_delta_str = f"{avg_delta:.1f}" if avg_delta is not None else "N/A"
             max_delta_str = f"{max_delta:.1f}" if max_delta is not None else "N/A"
             avg_peak_str = f"{avg_peak:.1f}" if avg_peak is not None else "N/A"
             max_peak_str = f"{max_peak:.1f}" if max_peak is not None else "N/A"

             console.print(f"[bold cyan]Server Memory (Batch):[/bold cyan] Avg Peak: {avg_peak_str} MB | Max Peak: {max_peak_str} MB | Avg Delta: {avg_delta_str} MB | Max Delta: {max_delta_str} MB (across {num_samples} requests)")
    else:
        console.print("[bold cyan]Server Memory:[/bold cyan] No memory data reported by server.")


    # No client memory report
    summary_path = pathlib.Path(args.report_path) / f"api_test_summary_{results['test_id']}.json"
    console.print(f"[bold green]Results summary saved to {summary_path}[/bold green]")

    if results["failed_requests"] > 0:
        console.print(f"\n[bold yellow]Warning: {results['failed_requests']} API requests failed ({100-success_rate_reqs:.1f}% failure rate)[/bold yellow]")
    if results["failed_urls"] > 0:
         console.print(f"[bold yellow]Warning: {results['failed_urls']} URLs failed to process ({100-success_rate_urls:.1f}% URL failure rate)[/bold yellow]")
    if results["total_urls_processed"] < results["url_count"]:
        console.print(f"\n[bold red]Error: Only {results['total_urls_processed']} out of {results['url_count']} target URLs were processed![/bold red]")
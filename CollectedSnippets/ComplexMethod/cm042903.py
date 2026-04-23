def main(
    preset: str = typer.Argument("quick", help="quick / debug / soak or custom"),
    api_url: str = typer.Option("http://localhost:8020", show_default=True),
    urls: int = typer.Option(None, help="Total URLs to crawl"),
    concurrent: int = typer.Option(None, help="Concurrent API requests"),
    chunk: int = typer.Option(None, help="URLs per request"),
    stream: bool = typer.Option(None, help="Use /crawl/stream"),
    report: pathlib.Path = typer.Option("reports_api", help="Where to save JSON summary"),
):
    """Run a stress test against a running Crawl4AI API server."""
    if preset not in PRESETS and any(v is None for v in (urls, concurrent, chunk, stream)):
        console.print(f"[red]Unknown preset '{preset}' and custom params missing[/]")
        raise typer.Exit(1)

    cfg = PRESETS.get(preset, {})
    urls = urls or cfg.get("urls")
    concurrent = concurrent or cfg.get("concurrent")
    chunk = chunk or cfg.get("chunk")
    stream = stream if stream is not None else cfg.get("stream", False)

    console.print(f"[cyan]API:[/] {api_url} | URLs: {urls} | Concurrency: {concurrent} | Chunk: {chunk} | Stream: {stream}")
    asyncio.run(_run(api_url, urls, concurrent, chunk, stream, report))
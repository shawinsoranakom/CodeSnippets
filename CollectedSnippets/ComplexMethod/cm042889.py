def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Crawl4AI SDK High Volume Stress Test using arun_many")

    # Test parameters
    parser.add_argument("--urls", type=int, default=DEFAULT_URL_COUNT, help=f"Number of URLs to test (default: {DEFAULT_URL_COUNT})")
    parser.add_argument("--max-sessions", type=int, default=DEFAULT_MAX_SESSIONS, help=f"Maximum concurrent crawling sessions (default: {DEFAULT_MAX_SESSIONS})")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"Number of URLs per batch for logging (default: {DEFAULT_CHUNK_SIZE})") # Added
    parser.add_argument("--stream", action="store_true", default=DEFAULT_STREAM_MODE, help=f"Enable streaming mode (disables batch logging) (default: {DEFAULT_STREAM_MODE})")
    parser.add_argument("--monitor-mode", type=str, default=DEFAULT_MONITOR_MODE, choices=["DETAILED", "AGGREGATED"], help=f"Display mode for the live monitor (default: {DEFAULT_MONITOR_MODE})")
    parser.add_argument("--use-rate-limiter", action="store_true", default=False, help="Enable a basic rate limiter (default: False)")

    # Environment parameters
    parser.add_argument("--site-path", type=str, default=DEFAULT_SITE_PATH, help=f"Path to generate/use the test site (default: {DEFAULT_SITE_PATH})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"Port for the local HTTP server (default: {DEFAULT_PORT})")
    parser.add_argument("--report-path", type=str, default=DEFAULT_REPORT_PATH, help=f"Path to save reports and logs (default: {DEFAULT_REPORT_PATH})")

    # Site/Server management
    parser.add_argument("--skip-generation", action="store_true", help="Use existing test site folder without regenerating")
    parser.add_argument("--use-existing-site", action="store_true", help="Do not generate site or start local server; assume site exists on --port")
    parser.add_argument("--keep-server-alive", action="store_true", help="Keep the local HTTP server running after test")
    parser.add_argument("--keep-site", action="store_true", help="Keep the generated test site files after test")
    parser.add_argument("--clean-reports", action="store_true", help="Clean up report directory before running")
    parser.add_argument("--clean-site", action="store_true", help="Clean up site directory before running (if generating) or after")

    args = parser.parse_args()

    # Display config
    console.print("[bold underline]Crawl4AI SDK Stress Test Configuration[/bold underline]")
    console.print(f"URLs: {args.urls}, Max Sessions: {args.max_sessions}, Chunk Size: {args.chunk_size}") # Added chunk size
    console.print(f"Mode: {'Streaming' if args.stream else 'Batch'}, Monitor: {args.monitor_mode}, Rate Limit: {args.use_rate_limiter}")
    console.print(f"Site Path: {args.site_path}, Port: {args.port}, Report Path: {args.report_path}")
    console.print("-" * 40)
    # (Rest of config display and cleanup logic is the same)
    if args.use_existing_site: console.print("[cyan]Mode: Using existing external site/server[/cyan]")
    elif args.skip_generation: console.print("[cyan]Mode: Using existing site files, starting local server[/cyan]")
    else: console.print("[cyan]Mode: Generating site files, starting local server[/cyan]")
    if args.keep_server_alive: console.print("[cyan]Option: Keep server alive after test[/cyan]")
    if args.keep_site: console.print("[cyan]Option: Keep site files after test[/cyan]")
    if args.clean_reports: console.print("[cyan]Option: Clean reports before test[/cyan]")
    if args.clean_site: console.print("[cyan]Option: Clean site directory[/cyan]")
    console.print("-" * 40)

    if args.clean_reports:
        if os.path.exists(args.report_path): console.print(f"[yellow]Cleaning up reports directory: {args.report_path}[/yellow]"); shutil.rmtree(args.report_path)
        os.makedirs(args.report_path, exist_ok=True)
    if args.clean_site and not args.use_existing_site:
         if os.path.exists(args.site_path): console.print(f"[yellow]Cleaning up site directory as requested: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)

    # Run
    try: asyncio.run(run_full_test(args))
    except KeyboardInterrupt: console.print("\n[bold yellow]Test interrupted by user.[/bold yellow]")
    except Exception as e: console.print(f"\n[bold red]An unexpected error occurred:[/bold red] {e}"); import traceback; traceback.print_exc()
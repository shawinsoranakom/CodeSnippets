async def run_full_test(args):
    """Run the complete test process from site generation to crawling."""
    server = None
    site_generated = False

    # --- Site Generation --- (Same as before)
    if not args.use_existing_site and not args.skip_generation:
        if os.path.exists(args.site_path): console.print(f"[yellow]Removing existing site directory: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
        site_generator = SiteGenerator(site_path=args.site_path, page_count=args.urls); site_generator.generate_site(); site_generated = True
    elif args.use_existing_site: console.print(f"[cyan]Using existing site assumed to be running on port {args.port}[/cyan]")
    elif args.skip_generation:
         console.print(f"[cyan]Skipping site generation, using existing directory: {args.site_path}[/cyan]")
         if not os.path.exists(args.site_path) or not os.path.isdir(args.site_path): console.print(f"[bold red]Error: Site path '{args.site_path}' does not exist or is not a directory.[/bold red]"); return

    # --- Start Local Server --- (Same as before)
    server_started = False
    if not args.use_existing_site:
        server = LocalHttpServer(site_path=args.site_path, port=args.port)
        try: server.start(); server_started = True
        except Exception as e:
            console.print(f"[bold red]Failed to start local server. Aborting test.[/bold red]")
            if site_generated and not args.keep_site: console.print(f"[yellow]Cleaning up generated site: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
            return

    try:
        # --- Run the Stress Test ---
        test = CrawlerStressTest(
            url_count=args.urls,
            port=args.port,
            max_sessions=args.max_sessions,
            chunk_size=args.chunk_size, # Pass chunk_size
            report_path=args.report_path,
            stream_mode=args.stream,
            monitor_mode=args.monitor_mode,
            use_rate_limiter=args.use_rate_limiter
        )
        results = await test.run() # Run the test which now handles chunks internally

        # --- Print Summary ---
        console.print("\n" + "=" * 80)
        console.print("[bold green]Test Completed[/bold green]")
        console.print("=" * 80)

        # (Summary printing logic remains largely the same)
        success_rate = results["successful_urls"] / results["url_count"] * 100 if results["url_count"] > 0 else 0
        urls_per_second = results["urls_processed"] / results["total_time_seconds"] if results["total_time_seconds"] > 0 else 0

        console.print(f"[bold cyan]Test ID:[/bold cyan] {results['test_id']}")
        console.print(f"[bold cyan]Configuration:[/bold cyan] {results['url_count']} URLs, {results['max_sessions']} sessions, Chunk: {results['chunk_size']}, Stream: {results['stream_mode']}, Monitor: {results['monitor_mode']}")
        console.print(f"[bold cyan]Results:[/bold cyan] {results['successful_urls']} successful, {results['failed_urls']} failed ({results['urls_processed']} processed, {success_rate:.1f}% success)")
        console.print(f"[bold cyan]Performance:[/bold cyan] {results['total_time_seconds']:.2f} seconds total, {urls_per_second:.2f} URLs/second avg")

        mem_report = results.get("memory", {})
        mem_info_str = "Memory tracking data unavailable."
        if mem_report and not mem_report.get("error"):
            start_mb = mem_report.get('start_memory_mb'); end_mb = mem_report.get('end_memory_mb'); max_mb = mem_report.get('max_memory_mb'); growth_mb = mem_report.get('memory_growth_mb')
            mem_parts = []
            if start_mb is not None: mem_parts.append(f"Start: {start_mb:.1f} MB")
            if end_mb is not None: mem_parts.append(f"End: {end_mb:.1f} MB")
            if max_mb is not None: mem_parts.append(f"Max: {max_mb:.1f} MB")
            if growth_mb is not None: mem_parts.append(f"Growth: {growth_mb:.1f} MB")
            if mem_parts: mem_info_str = ", ".join(mem_parts)
            csv_path = mem_report.get('csv_path')
            if csv_path: console.print(f"[dim]Memory samples saved to: {csv_path}[/dim]")

        console.print(f"[bold cyan]Memory Usage:[/bold cyan] {mem_info_str}")
        console.print(f"[bold green]Results summary saved to {results['memory']['csv_path'].replace('memory_samples', 'test_summary').replace('.csv', '.json')}[/bold green]") # Infer summary path


        if results["failed_urls"] > 0: console.print(f"\n[bold yellow]Warning: {results['failed_urls']} URLs failed to process ({100-success_rate:.1f}% failure rate)[/bold yellow]")
        if results["urls_processed"] < results["url_count"]: console.print(f"\n[bold red]Error: Only {results['urls_processed']} out of {results['url_count']} URLs were processed![/bold red]")


    finally:
        # --- Stop Server / Cleanup --- (Same as before)
        if server_started and server and not args.keep_server_alive: server.stop()
        elif server_started and server and args.keep_server_alive:
            console.print(f"[bold cyan]Server is kept running on port {args.port}. Press Ctrl+C to stop it.[/bold cyan]")
            try: await asyncio.Future() # Keep running indefinitely
            except KeyboardInterrupt: console.print("\n[bold yellow]Stopping server due to user interrupt...[/bold yellow]"); server.stop()

        if site_generated and not args.keep_site: console.print(f"[yellow]Cleaning up generated site: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
        elif args.clean_site and os.path.exists(args.site_path): console.print(f"[yellow]Cleaning up site directory as requested: {args.site_path}[/yellow]"); shutil.rmtree(args.site_path)
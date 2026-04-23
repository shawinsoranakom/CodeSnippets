def main():
    parser = argparse.ArgumentParser(description="Run a Crawl4AI SDK benchmark test and generate a report")

    # --- Arguments ---
    parser.add_argument("config", choices=list(TEST_CONFIGS) + ["custom"],
                        help="Test configuration: quick, small, medium, large, extreme, or custom")

    # Arguments for 'custom' config or to override presets
    parser.add_argument("--urls", type=int, help="Number of URLs")
    parser.add_argument("--max-sessions", type=int, help="Max concurrent sessions (replaces --workers)")
    parser.add_argument("--chunk-size", type=int, help="URLs per batch (for non-stream logging)")
    parser.add_argument("--port", type=int, help="HTTP server port")
    parser.add_argument("--monitor-mode", type=str, choices=["DETAILED", "AGGREGATED"], help="Monitor display mode")

    # Boolean flags / options
    parser.add_argument("--stream", action="store_true", help="Enable streaming results (disables batch logging)")
    parser.add_argument("--use-rate-limiter", action="store_true", help="Enable basic rate limiter")
    parser.add_argument("--no-report", action="store_true", help="Skip generating comparison report")
    parser.add_argument("--clean", action="store_true", help="Clean up reports and site before running")
    parser.add_argument("--keep-server-alive", action="store_true", help="Keep HTTP server running after test")
    parser.add_argument("--use-existing-site", action="store_true", help="Use existing site on specified port")
    parser.add_argument("--skip-generation", action="store_true", help="Use existing site files without regenerating")
    parser.add_argument("--keep-site", action="store_true", help="Keep generated site files after test")
    # Removed url_level_logging as it's implicitly handled by stream/batch mode now

    args = parser.parse_args()

    custom_args = {}

    # Populate custom_args from explicit command-line args
    if args.urls is not None: custom_args["urls"] = args.urls
    if args.max_sessions is not None: custom_args["max_sessions"] = args.max_sessions
    if args.chunk_size is not None: custom_args["chunk_size"] = args.chunk_size
    if args.port is not None: custom_args["port"] = args.port
    if args.monitor_mode is not None: custom_args["monitor_mode"] = args.monitor_mode
    if args.stream: custom_args["stream"] = True
    if args.use_rate_limiter: custom_args["use_rate_limiter"] = True
    if args.keep_server_alive: custom_args["keep_server_alive"] = True
    if args.use_existing_site: custom_args["use_existing_site"] = True
    if args.skip_generation: custom_args["skip_generation"] = True
    if args.keep_site: custom_args["keep_site"] = True
    # Clean flags are handled by the 'clean' argument passed to run_benchmark

    # Validate custom config requirements
    if args.config == "custom":
        required_custom = ["urls", "max_sessions", "chunk_size"]
        missing = [f"--{arg}" for arg in required_custom if arg not in custom_args]
        if missing:
            console.print(f"[bold red]Error: 'custom' config requires: {', '.join(missing)}[/bold red]")
            return 1

    success = run_benchmark(
        config_name=args.config,
        custom_args=custom_args, # Pass all collected custom args
        compare=not args.no_report,
        clean=args.clean
    )
    return 0 if success else 1
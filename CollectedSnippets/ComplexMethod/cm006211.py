def main():
    parser = argparse.ArgumentParser(
        description="Run Langflow load tests with automatic setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with web UI (interactive)
  python run_load_test.py

  # Run headless test with 50 users for 2 minutes
  python run_load_test.py --headless --users 50 --duration 120

  # Run with specific load shape
  python run_load_test.py --shape ramp100 --headless --users 100 --duration 180

  # Run against existing Langflow instance
  python run_load_test.py --host http://localhost:8000 --no-start-langflow

  # Save results to CSV
  python run_load_test.py --headless --csv results --users 25 --duration 60
        """,
    )

    # Langflow options
    parser.add_argument(
        "--host",
        default="http://localhost:7860",
        help="Langflow host URL (default: http://localhost:7860, use https:// for remote instances)",
    )
    parser.add_argument("--port", type=int, default=7860, help="Port to start Langflow on (default: 7860)")
    parser.add_argument(
        "--no-start-langflow",
        action="store_true",
        help="Don't start Langflow automatically (assume it's already running)",
    )

    # Load test options
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (no web UI)")
    parser.add_argument("--users", type=int, default=50, help="Number of concurrent users (default: 20)")
    parser.add_argument(
        "--spawn-rate", type=int, default=2, help="Rate to spawn users at (users per second, default: 2)"
    )
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds (default: 60)")
    parser.add_argument("--shape", choices=["ramp100", "stepramp"], help="Load test shape to use")
    parser.add_argument("--csv", help="Save results to CSV files with this prefix")
    parser.add_argument("--html", help="Generate HTML report with this filename (e.g., report.html)")

    args = parser.parse_args()

    # Check dependencies
    try:
        import httpx
        import locust
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install with: pip install locust httpx")
        sys.exit(1)

    langflow_process = None

    try:
        # Start Langflow if needed
        if not args.no_start_langflow:
            if args.host.startswith("https://") or not args.host.startswith("http://localhost"):
                print(f"⚠️  Remote host detected: {args.host}")
                print("   For remote instances, use --no-start-langflow flag")
                print("   Example: --host https://your-remote-instance.com --no-start-langflow")
                sys.exit(1)

            langflow_process = start_langflow(args.host, args.port)
            if not langflow_process:
                print("❌ Failed to start Langflow")
                sys.exit(1)
        # Just check if it's running
        elif not check_langflow_running(args.host):
            print(f"❌ Langflow is not running at {args.host}")
            if args.host.startswith("https://"):
                print("   Make sure your remote Langflow instance is accessible")
            else:
                print("Either start Langflow manually or remove --no-start-langflow flag")
            sys.exit(1)
        else:
            print(f"🔗 Using existing Langflow instance at {args.host}")
            if args.host.startswith("https://"):
                print("   ✅ Remote instance mode")

        # Test a single request before running the full load test
        if not test_single_request(args.host):
            print("❌ Single request test failed. Aborting load test.")
            sys.exit(1)

        # Run the load test
        run_locust_test(args)

    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        # Clean up Langflow process
        if langflow_process:
            print("\nStopping Langflow server...")
            langflow_process.terminate()
            try:
                langflow_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                langflow_process.kill()
            print("✅ Langflow server stopped")
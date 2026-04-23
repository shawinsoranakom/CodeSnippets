def run_locust_test(args):
    """Run the Locust load test."""
    locust_file = Path(__file__).parent / "langflow_locustfile.py"

    # Check for required environment variables
    if not os.getenv("API_KEY"):
        print("❌ API_KEY environment variable not found!")
        print("Run langflow_setup_test.py first to create test credentials.")
        sys.exit(1)

    if not os.getenv("FLOW_ID"):
        print("❌ FLOW_ID environment variable not found!")
        print("Run langflow_setup_test.py first to create test credentials.")
        sys.exit(1)

    cmd = [
        "locust",
        "-f",
        str(locust_file),
        "--host",
        args.host,
    ]

    # Add shape if specified
    env = os.environ.copy()
    if args.shape:
        env["SHAPE"] = args.shape

    # Add other environment variables
    env["LANGFLOW_HOST"] = args.host

    if args.headless:
        cmd.extend(
            [
                "--headless",
                "--users",
                str(args.users),
                "--spawn-rate",
                str(args.spawn_rate),
                "--run-time",
                f"{args.duration}s",
            ]
        )

    if args.csv:
        cmd.extend(["--csv", args.csv])

    if args.html:
        cmd.extend(["--html", args.html])

    print(f"\n{'=' * 60}")
    print("STARTING LOAD TEST")
    print(f"{'=' * 60}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Host: {args.host}")
    print(f"Users: {args.users}")
    print(f"Duration: {args.duration}s")
    print(f"Shape: {args.shape or 'default'}")
    print(f"API Key: {env.get('API_KEY', 'N/A')[:20]}...")
    print(f"Flow ID: {env.get('FLOW_ID', 'N/A')}")
    if args.html:
        print(f"HTML Report: {args.html}")
    if args.csv:
        print(f"CSV Reports: {args.csv}_*.csv")
    print(f"{'=' * 60}\n")

    subprocess.run(cmd, check=False, env=env)
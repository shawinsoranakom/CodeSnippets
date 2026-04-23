async def main() -> None:
    parser = argparse.ArgumentParser(
        prog="Benchmark serving with multi-turn conversations",
        description="Benchmark online inference using REST API",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")

    parser.add_argument(
        "-i",
        "--input-file",
        type=str,
        required=True,
        help="Input JSON file with ShareGPT conversations or "
        "configuration file for generation of synthetic conversations",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        type=str,
        default=None,
        help="Output JSON file containing conversations with updated assistant answers",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed for random number generators (default: 0)",
    )

    parser.add_argument(
        "-m", "--model", type=str, required=True, help="Path of the LLM model"
    )
    parser.add_argument(
        "--served-model-name",
        type=str,
        default=None,
        help="The model name used in the API. "
        "If not specified, the model name will be the "
        "same as the `--model` argument. ",
    )

    parser.add_argument(
        "-u",
        "--url",
        type=str,
        default="http://localhost:8000",
        help="Base URL for the LLM API server",
    )

    parser.add_argument(
        "-p",
        "--num-clients",
        type=int,
        default=1,
        help="Number of clients that will send requests in parallel",
    )
    parser.add_argument(
        "-k",
        "--max-active-conversations",
        type=int,
        default=None,
        help="Max number of active conversations at a time (for all clients)",
    )
    parser.add_argument(
        "-n",
        "--max-num-requests",
        type=int,
        default=None,
        help="Max number of requests to send (total for all clients)",
    )

    parser.add_argument(
        "--warmup-step",
        default=False,
        action="store_true",
        help="Run a warmup step (using only the first turn of every conversation), "
        "measurements will not be included in the final benchmark results",
    )

    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Maximum number of turns/messages per conversation, "
        "includes both user and assistant messages "
        "(a positive number, e.g: 2, 4, 6, etc.), disabled by default",
    )
    parser.add_argument(
        "--no-early-stop",
        default=False,
        action="store_true",
        help="By default, the benchmark will stop if at least one client exits."
        " Use this flag to disable this behavior",
    )

    parser.add_argument(
        "--limit-max-tokens",
        type=int,
        default=NUM_TOKENS_FROM_DATASET,
        help="Set max_tokens for the output token count of each request "
        "(must also set --limit-min-tokens). "
        "Overrides output token count from the input dataset. "
        "Use a negative value to disable this limit.",
    )
    parser.add_argument(
        "--limit-min-tokens",
        type=int,
        default=NUM_TOKENS_FROM_DATASET,
        help="Set min_tokens for the output token count of each request "
        "(must also set --limit-max-tokens). "
        "Overrides output token count from the input dataset. "
        "Use a negative value to disable this limit.",
    )

    parser.add_argument(
        "--request-rate",
        type=float,
        default=0,
        help="Expected request rate (Poisson process) per client in requests/sec."
        "Set to 0 for no delay between requests.",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=int(os.environ.get("MULTITURN_BENCH_MAX_RETRIES", "0")),
        help="Maximum number of retry attempts for timed-out requests. "
        "Default is 0 (no retries). "
        "Set to higher values to retry failed requests and maintain "
        "fair workload distribution. "
        "Can also be set via MULTITURN_BENCH_MAX_RETRIES environment variable.",
    )
    parser.add_argument(
        "--conversation-sampling",
        type=ConversationSampling,
        choices=list(ConversationSampling),
        default=ConversationSampling.ROUND_ROBIN,
        help=(
            "Strategy for selecting which conversation to use for the next request. "
            "Options: 'round_robin' (cycle through conversations), "
            "'random' (pick randomly)."
        ),
    )
    parser.add_argument(
        "--verify-output",
        default=False,
        action="store_true",
        help="Verify the LLM output (compare to the answers in the input JSON file)",
    )
    parser.add_argument(
        "--request-timeout-sec",
        type=int,
        default=120,
        help="Timeout in seconds for each API request (default: 120). "
        "Automatically increased if max tokens imply longer decoding.",
    )

    parser.add_argument(
        "--no-stream",
        default=False,
        action="store_true",
        help="Disable stream/streaming mode (set 'stream' to False in the API request)",
    )

    parser.add_argument(
        "-e",
        "--excel-output",
        default=False,
        action="store_true",
        help="Export summary to Excel file (optional)",
    )
    parser.add_argument(
        "--stats-json-output",
        type=str,
        default=None,
        help="Export per-request stats (ttft_ms, tpot_ms, etc.) to a JSON file",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        default=False,
        action="store_true",
        help="Enable verbose output",
    )
    parser.add_argument(
        "--print-content",
        default=False,
        action="store_true",
        help="Print the user prompts and the server's answers",
    )

    parser.add_argument(
        "--warmup-percentages",
        type=str,
        default="0%",
        help="Ignore the first X samples as warmup (X is a percentage)."
        " A comma separated list of percentages can be used "
        "(for example: --warmup-percentages=0%%,50%%)",
    )

    args = parser.parse_args()

    logger.info(args)

    logger.info(f"{Color.GREEN}Input parameters:{Color.RESET}")
    logger.info(f"url={args.url}")
    logger.info(f"model={args.model}")
    logger.info(f"num_clients={args.num_clients}")

    if args.verify_output:
        logger.info(f"{Color.PURPLE}Verify is enabled{Color.RESET}")

    # Calculate the amount of samples to filter (as warmup samples/measurements).
    try:
        warmup_percentages: list[float] = [0.0]
        if not args.warmup_step:
            # Warmup percentage can be used only if the warmup step was used
            warmup_strings: list[str] = args.warmup_percentages.split(",")
            warmup_strings = [x.replace("%", "") for x in warmup_strings]
            warmup_percentages = [float(x) / 100 for x in warmup_strings]

            # Check for valid range (0 to 1)
            for p in warmup_percentages:
                assert p >= 0.0 and p < 1.0

            # Sort from high to low warmup percentage
            warmup_percentages.sort()

            logger.info(
                f"Warmup percentages (percentage of samples): {warmup_percentages}"
            )

    except Exception:
        raise ValueError(
            f"Invalid --warmup-percentage={args.warmup_percentage}"
        ) from None

    # Set global seeds for main process
    random.seed(args.seed)
    np.random.seed(args.seed)

    logger.info("Loading tokenizer")
    tokenizer = AutoTokenizer.from_pretrained(args.model)

    await get_server_info(args.url)

    # Load the input file (either conversations of configuration file)
    logger.info(f"Reading input file: {args.input_file}")
    with open(args.input_file) as f:
        input_data = json.load(f)

    gen_conv_args = None
    if isinstance(input_data, list):
        # The conversations are stored as a list of dicts
        logger.info(f"Found {len(input_data)} items in the input file")

        # Convert the list to a ConversationsMap
        conversations = conversations_list_to_dict(input_data)

    elif isinstance(input_data, dict):
        # The input file is a configuration file
        # (type is determined by the field 'filetype')
        if "filetype" not in input_data:
            raise Exception(
                f"Input file {args.input_file} is invalid (missing 'filetype')"
            )

        logger.info(f"Using input file with filetype: {input_data['filetype']}")

        gen_conv_args = parse_input_json_file(input_data)

        # Disable warning from "huggingface/tokenizers"
        # (when using python multiprocessing and tokenizers)
        os.environ["TOKENIZERS_PARALLELISM"] = "true"

        # Generate synthetic conversations
        conversations = generate_conversations(gen_conv_args, tokenizer)

    else:
        raise Exception(f"Input file {args.input_file} is invalid")

    if args.max_turns is not None:
        if args.max_turns < 1:
            raise ValueError("Max turns must be a positive number")
        logger.info(
            f"{Color.PURPLE}Max turns per conversation "
            f"is limited to {args.max_turns}{Color.RESET}"
        )

    # Create benchmark configurations
    client_args, req_args = get_client_config(args, conversations)

    bench_args = BenchmarkArgs(
        url=args.url, num_clients=args.num_clients, early_stop=not args.no_early_stop
    )

    warmup_runtime_sec: float | None = None

    # Warm-up step
    if args.warmup_step:
        # Only send a single user prompt from every conversation.
        # max_active_conversations must be 1,
        # otherwise the clients may exit after sending a single request
        # (because the task queue is empty).
        warmup_client_args = client_args._replace(
            skip_first_turn=False, max_turns=1, max_active_conversations=1
        )

        # Early stop should be disabled,
        # all clients should finish their work before exiting
        warmup_bench_args = bench_args._replace(early_stop=False)

        logger.info("%sWarmup start%s", Color.PURPLE, Color.RESET)
        warmup_start_ns = time.perf_counter_ns()
        conversations, _ = await main_mp(
            warmup_client_args, req_args, warmup_bench_args, tokenizer, conversations
        )
        warmup_runtime_sec = nanosec_to_sec(time.perf_counter_ns() - warmup_start_ns)
        logger.info(
            "%sWarmup runtime: %.3f sec (%.3f ms)%s",
            Color.PURPLE,
            warmup_runtime_sec,
            warmup_runtime_sec * 1000,
            Color.RESET,
        )
        logger.info("%sWarmup done%s", Color.PURPLE, Color.RESET)

    # Run the benchmark
    benchmark_start_ns = time.perf_counter_ns()
    client_convs, client_metrics = await main_mp(
        client_args, req_args, bench_args, tokenizer, conversations
    )
    benchmark_runtime_sec = nanosec_to_sec(time.perf_counter_ns() - benchmark_start_ns)

    # Calculate requests per second
    requests_per_sec = len(client_metrics) / benchmark_runtime_sec
    benchmark_runtime_ms = benchmark_runtime_sec * 1000.0
    logger.info(
        "%sAll clients finished, benchmark runtime: %.3f sec (%.3f ms), "
        "requests per second: %.3f%s",
        Color.GREEN,
        benchmark_runtime_sec,
        benchmark_runtime_ms,
        requests_per_sec,
        Color.RESET,
    )
    if warmup_runtime_sec is not None:
        total_runtime_sec = benchmark_runtime_sec + warmup_runtime_sec
        logger.info(
            "%sWarmup runtime: %.3f sec (%.3f ms)%s",
            Color.GREEN,
            warmup_runtime_sec,
            warmup_runtime_sec * 1000,
            Color.RESET,
        )
        logger.info(
            "%sTotal runtime (including warmup): %.3f sec (%.3f ms)%s",
            Color.GREEN,
            total_runtime_sec,
            total_runtime_sec * 1000,
            Color.RESET,
        )

    # Benchmark parameters
    params = {
        "model": args.model,
        "num_clients": args.num_clients,
        "num_conversations": len(conversations),
        "active_conversations": args.max_active_conversations,
        "seed": args.seed,
    }

    if args.limit_min_tokens > 0:
        params["min_tokens"] = args.limit_min_tokens

    if args.limit_max_tokens > 0:
        params["max_tokens"] = args.limit_max_tokens

    # Process and print statistics (and save excel file with the statistics)
    process_statistics(
        client_metrics,
        test_params=params,
        warmup_percentages=warmup_percentages,
        verbose=args.verbose,
        gen_conv_args=gen_conv_args,
        excel_output=args.excel_output,
        warmup_runtime_sec=warmup_runtime_sec,
    )

    if args.stats_json_output is not None:
        # Export per-request metrics as a JSON array for downstream analysis.
        stats_data = [s._asdict() for s in client_metrics]
        logger.info(
            f"{Color.GREEN}Writing per-request stats JSON: "
            f"{args.stats_json_output}{Color.RESET}"
        )
        os.makedirs(
            os.path.dirname(os.path.abspath(args.stats_json_output)), exist_ok=True
        )
        with open(args.stats_json_output, "w") as f:
            json.dump(stats_data, f, indent=2)

    if args.output_file is not None:
        # Write a JSON file with the updated conversations
        # The "assistant" content will contain the answers from the tested LLM
        output_data: ShareGptConversations = conversations_dict_to_list(client_convs)
        logger.info(
            f"{Color.GREEN}Writing conversations file: {args.output_file}{Color.RESET}"
        )
        with open(args.output_file, "w") as f:
            json.dump(output_data, f, indent=4)
def get_client_config(
    args: argparse.Namespace, input_conv: ConversationsMap
) -> tuple[ClientArgs, RequestArgs]:
    if args.num_clients < 1:
        raise ValueError("Number of clients must be a positive number")

    if len(input_conv) < args.num_clients:
        raise ValueError(
            "Number of conversations must be equal or larger than the number of clients"
        )

    max_req_per_client: int | None = None
    if args.max_num_requests is not None:
        # Max number of requests per client
        req_per_client = args.max_num_requests // args.num_clients
        if req_per_client < 1:
            raise ValueError("Number of requests should be at least one per client")
        max_req_per_client = req_per_client

    max_active_conversations = args.max_active_conversations
    if max_active_conversations is None:
        # Each client will have only one active conversation at a time
        max_active_conversations = args.num_clients

    if max_active_conversations > len(input_conv):
        raise ValueError(
            f"Max active conversations {max_active_conversations} "
            "must be equal or less than the total number of conversations"
        )

    # Max number of active conversations per client
    max_active_conv_per_client = max_active_conversations // args.num_clients
    if max_active_conv_per_client < 1:
        raise ValueError(
            f"Max active conversations {max_active_conversations} "
            "must be equal or greater than the number of clients"
        )

    # Skip the first user turn (as part of the warmup)
    skip_first_turn = args.warmup_step

    # Common arguments for all clients
    client_args = ClientArgs(
        seed=args.seed,
        max_num_requests=max_req_per_client,
        skip_first_turn=skip_first_turn,
        max_turns=args.max_turns,
        max_active_conversations=max_active_conv_per_client,
        verbose=args.verbose,
        print_content=args.print_content,
        verify_output=args.verify_output,
        conversation_sampling=args.conversation_sampling,
        request_rate=args.request_rate,
        max_retries=args.max_retries,
    )

    if args.limit_min_tokens > 0 or args.limit_max_tokens > 0:
        if args.limit_min_tokens < 1 or args.limit_max_tokens < 1:
            raise ValueError(
                "Invalid min/max tokens limits (both limits should be provided)"
            )
        if args.limit_min_tokens > args.limit_max_tokens:
            raise ValueError(
                "Invalid min/max tokens limits (min should not be larger than max)"
            )

    if args.request_timeout_sec <= 0:
        raise ValueError("Request timeout must be a positive number")

    # Arguments for API requests
    chat_url = f"{args.url}/v1/chat/completions"
    model_name = args.served_model_name if args.served_model_name else args.model

    req_args = RequestArgs(
        chat_url=chat_url,
        model=model_name,
        stream=not args.no_stream,
        limit_min_tokens=args.limit_min_tokens,
        limit_max_tokens=args.limit_max_tokens,
        timeout_sec=args.request_timeout_sec,
    )

    return client_args, req_args
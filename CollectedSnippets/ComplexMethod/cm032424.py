def run_chat(client: HttpClient, args: argparse.Namespace) -> int:
    document_paths = _load_paths(args)
    needs_dataset = bool(document_paths)
    dataset_info = _prepare_dataset(client, args, needs_dataset, document_paths)
    created = dict(dataset_info["created"])
    dataset_id = dataset_info["dataset_id"]
    dataset_ids = dataset_info["dataset_ids"]
    doc_ids = []
    if dataset_id and document_paths:
        doc_ids = _maybe_upload_and_parse(client, dataset_id, document_paths, args.parse_timeout, args.parse_interval)
        created["Created Document IDs"] = ",".join(doc_ids)
    if dataset_id and not document_paths:
        _ensure_dataset_has_chunks(client, dataset_id)
    if dataset_id and not document_paths and dataset_ids:
        _ensure_dataset_has_chunks(client, dataset_id)

    chat_payload = load_json_arg(args.chat_payload, "chat-payload") if args.chat_payload else None
    chat_id = args.chat_id
    if not chat_id:
        if not args.chat_name and not (chat_payload and chat_payload.get("name")):
            raise ChatError("Missing --chat-name or chat payload name")
        chat_name = args.chat_name or chat_payload.get("name")
        chat_data = create_chat(client, chat_name, dataset_ids or [], chat_payload)
        chat_id = chat_data.get("id")
        if not chat_id:
            raise ChatError("Chat creation did not return id")
        created["Created Chat ID"] = chat_id
    chat_data = get_chat(client, chat_id)
    model = resolve_model(args.model, chat_data)

    messages = None
    if args.messages_json:
        messages = load_json_arg(args.messages_json, "messages-json")
    if not messages:
        if not args.message:
            raise ChatError("Missing --message or --messages-json")
        messages = [{"role": "user", "content": args.message}]
    extra_body = load_json_arg(args.extra_body, "extra-body") if args.extra_body else None

    samples: List[ChatSample] = []
    responses: List[str] = []
    start_time = time.perf_counter()
    if args.concurrency <= 1:
        for _ in range(args.iterations):
            samples.append(stream_chat_completion(client, chat_id, model, messages, extra_body))
    else:
        results: List[Optional[ChatSample]] = [None] * args.iterations
        mp_context = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.concurrency, mp_context=mp_context) as executor:
            future_map = {
                executor.submit(
                    _chat_worker,
                    client.base_url,
                    client.api_version,
                    client.api_key or "",
                    client.connect_timeout,
                    client.read_timeout,
                    client.verify_ssl,
                    chat_id,
                    model,
                    messages,
                    extra_body,
                ): idx
                for idx in range(args.iterations)
            }
            for future in as_completed(future_map):
                idx = future_map[future]
                results[idx] = future.result()
        samples = [sample for sample in results if sample is not None]
    total_duration = time.perf_counter() - start_time
    if args.print_response:
        for idx, sample in enumerate(samples, start=1):
            rendered = _format_chat_response(sample, args.response_max_chars)
            if args.json:
                responses.append(rendered)
            else:
                print(f"Response[{idx}]: {rendered}")

    total_latencies = [s.total_latency for s in samples if s.total_latency is not None and s.error is None]
    first_latencies = [s.first_token_latency for s in samples if s.first_token_latency is not None and s.error is None]
    success = len(total_latencies)
    failure = len(samples) - success
    errors = [s.error for s in samples if s.error]

    total_stats = summarize(total_latencies)
    first_stats = summarize(first_latencies)
    if args.json:
        payload = {
            "interface": "chat",
            "concurrency": args.concurrency,
            "iterations": args.iterations,
            "success": success,
            "failure": failure,
            "model": model,
            "total_latency": total_stats,
            "first_token_latency": first_stats,
            "errors": [e for e in errors if e],
            "created": created,
            "total_duration_s": total_duration,
            "qps": (args.iterations / total_duration) if total_duration > 0 else None,
        }
        if args.print_response:
            payload["responses"] = responses
        print(json.dumps(payload, sort_keys=True))
    else:
        report = chat_report(
            interface="chat",
            concurrency=args.concurrency,
            total_duration_s=total_duration,
            iterations=args.iterations,
            success=success,
            failure=failure,
            model=model,
            total_stats=total_stats,
            first_token_stats=first_stats,
            errors=[e for e in errors if e],
            created=created,
        )
        print(report, end="")
    _cleanup(client, created, args.teardown)
    return 0 if failure == 0 else 1
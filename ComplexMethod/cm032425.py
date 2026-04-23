def run_retrieval(client: HttpClient, args: argparse.Namespace) -> int:
    document_paths = _load_paths(args)
    needs_dataset = True
    dataset_info = _prepare_dataset(client, args, needs_dataset, document_paths)
    created = dict(dataset_info["created"])
    dataset_id = dataset_info["dataset_id"]
    dataset_ids = dataset_info["dataset_ids"]
    if not dataset_ids:
        raise RetrievalError("dataset_ids required for retrieval")

    doc_ids = []
    if dataset_id and document_paths:
        doc_ids = _maybe_upload_and_parse(client, dataset_id, document_paths, args.parse_timeout, args.parse_interval)
        created["Created Document IDs"] = ",".join(doc_ids)

    payload_override = load_json_arg(args.payload, "payload") if args.payload else None
    question = args.question
    if not question and (payload_override is None or "question" not in payload_override):
        raise RetrievalError("Missing --question or retrieval payload question")
    document_ids = split_csv(args.document_ids) if args.document_ids else None

    payload = build_payload(question, dataset_ids, document_ids, payload_override)

    samples: List[RetrievalSample] = []
    responses: List[str] = []
    start_time = time.perf_counter()
    if args.concurrency <= 1:
        for _ in range(args.iterations):
            samples.append(run_retrieval_request(client, payload))
    else:
        results: List[Optional[RetrievalSample]] = [None] * args.iterations
        mp_context = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=args.concurrency, mp_context=mp_context) as executor:
            future_map = {
                executor.submit(
                    _retrieval_worker,
                    client.base_url,
                    client.api_version,
                    client.api_key or "",
                    client.connect_timeout,
                    client.read_timeout,
                    client.verify_ssl,
                    payload,
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
            rendered = _format_retrieval_response(sample, args.response_max_chars)
            if args.json:
                responses.append(rendered)
            else:
                print(f"Response[{idx}]: {rendered}")

    latencies = [s.latency for s in samples if s.latency is not None and s.error is None]
    success = len(latencies)
    failure = len(samples) - success
    errors = [s.error for s in samples if s.error]

    stats = summarize(latencies)
    if args.json:
        payload = {
            "interface": "retrieval",
            "concurrency": args.concurrency,
            "iterations": args.iterations,
            "success": success,
            "failure": failure,
            "latency": stats,
            "errors": [e for e in errors if e],
            "created": created,
            "total_duration_s": total_duration,
            "qps": (args.iterations / total_duration) if total_duration > 0 else None,
        }
        if args.print_response:
            payload["responses"] = responses
        print(json.dumps(payload, sort_keys=True))
    else:
        report = retrieval_report(
            interface="retrieval",
            concurrency=args.concurrency,
            total_duration_s=total_duration,
            iterations=args.iterations,
            success=success,
            failure=failure,
            stats=stats,
            errors=[e for e in errors if e],
            created=created,
        )
        print(report, end="")
    _cleanup(client, created, args.teardown)
    return 0 if failure == 0 else 1
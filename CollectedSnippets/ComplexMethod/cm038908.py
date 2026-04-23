def main(args: argparse.Namespace):
    print(args)
    random.seed(args.seed)
    np.random.seed(args.seed)

    backend = args.backend
    model_id = args.model
    tokenizer_id = args.tokenizer if args.tokenizer is not None else args.model

    if args.base_url is not None:
        api_url = f"{args.base_url}{args.endpoint}"
        base_url = f"{args.base_url}"
    else:
        api_url = f"http://{args.host}:{args.port}{args.endpoint}"
        base_url = f"http://{args.host}:{args.port}"

    tokenizer = get_tokenizer(
        tokenizer_id,
        trust_remote_code=args.trust_remote_code,
        tokenizer_mode=args.tokenizer_mode,
    )

    if args.dataset == "grammar":
        args.structure_type = "grammar"
    elif args.dataset == "regex":
        args.structure_type = "regex"
    elif args.dataset == "choice":
        args.structure_type = "choice"
    else:
        args.structure_type = "json"

    if args.no_structured_output:
        args.structured_output_ratio = 0
    if args.save_results:
        result_file_name = f"{args.structured_output_ratio}so"
        result_file_name += f"_{backend}"
        result_file_name += f"_{args.request_rate}qps"
        result_file_name += f"_{args.model.split('/')[-1]}"
        result_file_name += f"_{args.dataset}"
        result_file_name += f"_{args.num_prompts}"
        result_file_name += f"_out{args.output_len}"
        result_file_name += ".txt"
    else:
        result_file_name = None

    input_requests = sample_requests(tokenizer, args)

    goodput_config_dict = check_goodput_args(args)

    benchmark_result, ret = asyncio.run(
        benchmark(
            backend=backend,
            api_url=api_url,
            base_url=base_url,
            model_id=model_id,
            tokenizer=tokenizer,
            input_requests=input_requests,
            request_rate=args.request_rate,
            burstiness=args.burstiness,
            disable_tqdm=args.disable_tqdm,
            profile=args.profile,
            selected_percentile_metrics=args.percentile_metrics.split(","),
            selected_percentiles=[float(p) for p in args.metric_percentiles.split(",")],
            ignore_eos=args.ignore_eos,
            max_concurrency=args.max_concurrency,
            structured_output_ratio=args.structured_output_ratio,
            goodput_config_dict=goodput_config_dict,
        )
    )

    # Save config and results to json
    score = evaluate(ret, args)
    print("correct_rate(%)", score, "\n")
    if args.save_results:
        results = {
            "backend": backend,
            "model_id": model_id,
            "tokenizer_id": tokenizer_id,
            "num_prompts": args.num_prompts,
            "request_rate": args.request_rate
            if args.request_rate < float("inf")
            else "inf",
            "burstiness": args.burstiness,
            "max_concurrency": args.max_concurrency,
            "correct_rate(%)": score,
        }
        results = {"outputs": ret, **results, **benchmark_result}

        # Save to file
        if args.result_filename:
            result_file_name = args.result_filename
        if args.result_dir:
            result_file_name = os.path.join(args.result_dir, result_file_name)
        with open(result_file_name, "w", encoding="utf-8") as outfile:
            json.dump(results, outfile, indent=4)
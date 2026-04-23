def evaluate_model_aime(
    model,
    tokenizer,
    model_type = "base",
    lora_request = None,
    temperature = 0.3,
    n_sampling = 8,
    max_tokens = 32768,
    top_p = 0.95,
    seed = 0,
):
    """Evaluate model on combined AIME dataset with official configuration"""

    print(f"\n{'='*70}")
    print(f"🧮 AIME EVALUATION - {model_type.upper()} MODEL")
    print(f"Combined Dataset: test2024 + test2025-I + test2025-II")
    print(f"{'='*70}")

    # Load combined AIME dataset
    try:
        eval_dataset = load_aime_dataset()
    except Exception as e:
        print(f"Error loading dataset: {e}")
        return None

    if not eval_dataset:
        print("No examples found in dataset")
        return None

    # Initialize tracking variables
    records = {}
    input_tokens = []
    output_tokens = []
    correct_answers = 0

    # Track performance by source dataset
    source_stats = {}
    for example in eval_dataset:
        source = example["source_dataset"]
        if source not in source_stats:
            source_stats[source] = {"total": 0, "correct": 0}
        source_stats[source]["total"] += 1

    # Setup sampling parameters (AIME configuration)
    sampling_params = SamplingParams(
        temperature = temperature,
        top_p = top_p,
        max_tokens = max_tokens,
        n = n_sampling,  # Multiple samples per question
        seed = seed,
    )

    print(f"\n🔧 Configuration:")
    print(f"   Temperature: {temperature}")
    print(f"   Samples per question: {n_sampling}")
    print(f"   Max tokens: {max_tokens}")
    print(f"   Top-p: {top_p}")
    print(f"   Seed: {seed}")

    # Temporarily suppress verbose logging
    original_levels = {}
    loggers_to_suppress = [
        "vllm",
        "vllm.engine",
        "vllm.worker",
        "vllm.model_executor",
        "vllm.executor",
        "ray",
    ]

    for logger_name in loggers_to_suppress:
        logger = logging.getLogger(logger_name)
        original_levels[logger_name] = logger.level
        logger.setLevel(logging.WARNING)

    try:
        print(f"\n🚀 Evaluating {len(eval_dataset)} problems...")

        # Main evaluation loop
        with tqdm(
            total = len(eval_dataset), desc = "Processing AIME problems", unit = "problem"
        ) as pbar:
            for task_id, item in enumerate(eval_dataset):
                try:
                    # Prepare prompt
                    prompt_text = tokenizer.apply_chat_template(
                        item["prompt"], add_generation_prompt = True, tokenize = False
                    )

                    input_tokens.append(get_num_tokens(prompt_text, tokenizer))

                    # Generate multiple responses
                    outputs = model.fast_generate(
                        [prompt_text],
                        sampling_params = sampling_params,
                        lora_request = lora_request,
                        use_tqdm = False,
                    )[0].outputs

                    # Process all generated responses
                    responses = [output.text for output in outputs]
                    extracted_answers = [
                        extract_aime_answer(response) for response in responses
                    ]

                    # Calculate total output tokens
                    total_output_tokens = sum(
                        get_num_tokens(response, tokenizer) for response in responses
                    )
                    output_tokens.append(total_output_tokens)

                    # Check if any answer is correct
                    ground_truth = item["answer"]
                    correct_responses = [
                        ans == ground_truth for ans in extracted_answers
                    ]
                    is_correct = any(correct_responses)

                    if is_correct:
                        correct_answers += 1
                        source_stats[item["source_dataset"]]["correct"] += 1

                    # Store detailed record
                    records[task_id] = {
                        "global_id": item["global_id"],
                        "original_id": item["original_id"],
                        "source_dataset": item["source_dataset"],
                        "problem": item["problem"],
                        "ground_truth": ground_truth,
                        "responses": responses,
                        "extracted_answers": extracted_answers,
                        "correct_responses": correct_responses,
                        "is_correct": is_correct,
                        "input_tokens": input_tokens[-1],
                        "output_tokens": total_output_tokens,
                        "n_correct": sum(correct_responses),
                        "n_total": len(responses),
                        "solution": item.get("solution", ""),
                        "url": item.get("url", ""),
                    }

                    # Update progress
                    current_accuracy = correct_answers / (task_id + 1) * 100
                    pbar.set_postfix(
                        {
                            "accuracy": f"{current_accuracy:.1f}%",
                            "correct": correct_answers,
                            "total": task_id + 1,
                        }
                    )
                    pbar.update(1)

                except Exception as e:
                    print(f"\nError processing problem {task_id}: {str(e)}")
                    records[task_id] = {
                        "global_id": item.get("global_id", task_id),
                        "original_id": item.get("original_id", task_id),
                        "source_dataset": item.get("source_dataset", "unknown"),
                        "problem": item["problem"],
                        "ground_truth": item["answer"],
                        "error": str(e),
                        "is_correct": False,
                    }
                    pbar.update(1)
                    continue

    finally:
        # Restore logging levels
        for logger_name, level in original_levels.items():
            logging.getLogger(logger_name).setLevel(level)

    # Calculate metrics
    total_problems = len(eval_dataset)
    accuracy = correct_answers / total_problems * 100

    # Calculate Pass@k (probability that at least one of k samples is correct)
    pass_at_k_scores = []
    for record in records.values():
        if "n_correct" in record and "n_total" in record:
            n_correct = record["n_correct"]
            n_total = record["n_total"]
            if n_correct > 0:
                pass_at_k_scores.append(1.0)
            else:
                pass_at_k_scores.append(0.0)

    pass_at_k = sum(pass_at_k_scores) / len(pass_at_k_scores) if pass_at_k_scores else 0

    # Calculate per-source accuracies
    source_accuracies = {}
    for source, stats in source_stats.items():
        source_accuracies[source] = (
            (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        )

    results = {
        "model_type": model_type,
        "dataset": "aime_combined",
        "total_problems": total_problems,
        "correct_answers": correct_answers,
        "accuracy": accuracy,
        "pass_at_k": pass_at_k * 100,
        "source_stats": source_stats,
        "source_accuracies": source_accuracies,
        "temperature": temperature,
        "n_sampling": n_sampling,
        "max_tokens": max_tokens,
        "top_p": top_p,
        "seed": seed,
        "avg_input_tokens": sum(input_tokens) / len(input_tokens)
        if input_tokens
        else 0,
        "avg_output_tokens": sum(output_tokens) / len(output_tokens)
        if output_tokens
        else 0,
        "max_input_tokens": max(input_tokens) if input_tokens else 0,
        "max_output_tokens": max(output_tokens) if output_tokens else 0,
    }

    # Save results
    filename = f"aime_eval_combined_{model_type}_t{temperature}_n{n_sampling}.json"
    with open(filename, "w", encoding = "utf-8") as f:
        json.dump({"results": results, "records": records}, f, indent = 4)

    # Print comprehensive summary
    print(f"\n{'='*70}")
    print(f"📊 AIME EVALUATION RESULTS - {model_type.upper()}")
    print(f"{'='*70}")

    print(f"\n🎯 Overall Performance:")
    print(f"   Total problems:       {total_problems:>6}")
    print(
        f"   Correct answers:      {correct_answers:>6}/{total_problems} ({accuracy:>5.1f}%)"
    )
    print(f"   Pass@{n_sampling}:              {pass_at_k:>10.1f}%")

    print(f"\n📈 Performance by Dataset:")
    for source, stats in source_stats.items():
        source_acc = source_accuracies[source]
        print(
            f"   {source:>12}: {stats['correct']:>3}/{stats['total']:>3} ({source_acc:>5.1f}%)"
        )

    print(f"\n🔧 Configuration:")
    print(f"   Temperature:          {temperature}")
    print(f"   Samples per problem:  {n_sampling}")
    print(f"   Max tokens:           {max_tokens}")
    print(f"   Top-p:                {top_p}")
    print(f"   Seed:                 {seed}")

    print(f"\n📝 Token Statistics:")
    print(f"   Avg input tokens:     {results['avg_input_tokens']:>10.1f}")
    print(f"   Avg output tokens:    {results['avg_output_tokens']:>10.1f}")
    print(f"   Max input tokens:     {results['max_input_tokens']:>10}")
    print(f"   Max output tokens:    {results['max_output_tokens']:>10}")

    # Performance assessment for AIME
    if accuracy >= 50:
        tier = "🏆 EXCEPTIONAL"
    elif accuracy >= 30:
        tier = "✅ EXCELLENT"
    elif accuracy >= 20:
        tier = "🎯 VERY GOOD"
    elif accuracy >= 10:
        tier = "⚠️  GOOD"
    elif accuracy >= 5:
        tier = "📈 FAIR"
    else:
        tier = "❌ NEEDS IMPROVEMENT"

    print(f"\n🎖️  AIME Performance:     {tier} ({accuracy:.1f}%)")
    print(f"\n💾 Detailed results saved to: {filename}")
    print(f"\n{'='*70}")

    return results
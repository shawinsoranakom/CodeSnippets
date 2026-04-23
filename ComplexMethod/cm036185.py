def main():
    """Main test function."""
    parser = argparse.ArgumentParser(
        description="EPD correctness test - compare disagg vs baseline"
    )

    parser.add_argument(
        "--service_url",
        type=str,
        required=True,
        help="The vLLM service URL (e.g., http://localhost:8000)",
    )

    parser.add_argument(
        "--model_name",
        type=str,
        required=True,
        help="Model name",
    )

    parser.add_argument(
        "--mode",
        type=str,
        default="baseline",
        choices=["baseline", "baseline_pd", "disagg"],
        help="Mode: baseline/baseline_pd (saves outputs) or disagg (compares outputs)",
    )

    parser.add_argument(
        "--baseline_file",
        type=str,
        default=".vllm_epd_baseline.txt",
        help="File to save/load baseline outputs",
    )

    parser.add_argument(
        "--use_mm_prompts",
        action="store_true",
        help="Use multimodal prompts (default: use text-only for quick testing)",
    )

    args = parser.parse_args()

    print(f"Service URL: {args.service_url}")
    print(f"Model: {args.model_name}")
    print(f"Mode: {args.mode}")
    print(f"Output file: {args.baseline_file}")
    print(f"Use MM prompts: {args.use_mm_prompts}")

    # Determine health check endpoint
    if args.mode == "baseline":
        health_check_url = f"{args.service_url}/health"
    elif args.mode == "baseline_pd":
        # Nixl toy proxy use /healthcheck
        health_check_url = f"{args.service_url}/healthcheck"
    else:
        # Disagg EPD proxy uses /health
        health_check_url = f"{args.service_url}/health"
        if not os.path.exists(args.baseline_file):
            raise ValueError(
                f"In disagg mode, the output file {args.baseline_file} from "
                "baseline does not exist. Run baseline mode first."
            )

    # Check if server is ready
    if not check_vllm_server(health_check_url):
        raise RuntimeError(f"vLLM server at {args.service_url} is not ready!")

    # Select prompts to use
    if args.use_mm_prompts:
        test_prompts = SAMPLE_PROMPTS_MM
        print("Using multimodal prompts")
    else:
        test_prompts = SAMPLE_PROMPTS_TEXT
        print("Using text-only prompts for quick testing")

    # Run completions
    service_url = f"{args.service_url}/v1"
    output_strs = {}

    for i, prompt_data in enumerate(test_prompts):
        print(
            f"\nRunning prompt {i + 1}/{len(test_prompts)}: "
            f"{prompt_data['description']}"
        )

        output_str = run_chat_completion(
            base_url=service_url,
            model_name=args.model_name,
            messages=prompt_data["messages"],
            max_tokens=MAX_OUTPUT_LEN,
        )

        # Use description as key for comparison
        key = prompt_data["description"]
        output_strs[key] = output_str
        print(f"Output: {output_str}")

    if args.mode in ("baseline", "baseline_pd"):
        # Baseline mode: Save outputs
        print(f"\nSaving baseline outputs to {args.baseline_file}")
        try:
            with open(args.baseline_file, "w") as json_file:
                json.dump(output_strs, json_file, indent=4)
            print("✅ Baseline outputs saved successfully")
        except OSError as e:
            print(f"Error writing to file: {e}")
            raise
    else:
        # Disagg mode: Load and compare outputs
        print(f"\nLoading baseline outputs from {args.baseline_file}")
        baseline_outputs = None
        try:
            with open(args.baseline_file) as json_file:
                baseline_outputs = json.load(json_file)
        except OSError as e:
            print(f"Error reading from file: {e}")
            raise

        # Verify outputs match
        print("\nComparing disagg outputs with baseline...")
        assert isinstance(baseline_outputs, dict), "Baseline outputs should be a dict"
        assert len(baseline_outputs) == len(output_strs), (
            f"Length mismatch: baseline has {len(baseline_outputs)}, "
            f"disagg has {len(output_strs)}"
        )

        all_match = True
        for key, baseline_output in baseline_outputs.items():
            assert key in output_strs, f"{key} not in disagg outputs"

            disagg_output = output_strs[key]
            if baseline_output == disagg_output:
                print(f"✅ {key}: MATCH")
            else:
                print(f"❌ {key}: MISMATCH")
                print(f"  Baseline: {baseline_output}")
                print(f"  Disagg:   {disagg_output}")
                all_match = False

        assert all_match, "❌❌Disagg outputs do not match baseline!❌❌"
        if all_match:
            print("\n✅ All outputs match! Test PASSED")
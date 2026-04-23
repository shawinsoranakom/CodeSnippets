def main():
    """
    This script demonstrates how to accept two optional string arguments
    ("service_url" and "file_name") from the command line, each with a
    default value of an empty string, using the argparse module.
    """
    parser = argparse.ArgumentParser(description="vLLM client script")

    parser.add_argument(
        "--service_url",  # Name of the first argument
        type=str,
        required=True,
        help="The vLLM service URL.",
    )

    parser.add_argument(
        "--model_name",  # Name of the first argument
        type=str,
        required=True,
        help="model_name",
    )

    parser.add_argument(
        "--mode",  # Name of the second argument
        type=str,
        default="baseline",
        help="mode: baseline==non-disagg, or disagg",
    )

    parser.add_argument(
        "--file_name",  # Name of the second argument
        type=str,
        default=".vllm_output.txt",
        help="the file that saves the output tokens ",
    )

    args = parser.parse_args()

    for arg in vars(args):
        print(f"{arg}: {getattr(args, arg)}")

    if args.mode == "baseline":
        # non-disagg
        health_check_url = f"{args.service_url}/health"
    else:
        # disagg proxy
        health_check_url = f"{args.service_url}/healthcheck"
        if not os.path.exists(args.file_name):
            raise ValueError(
                f"In disagg mode, the output file {args.file_name} from "
                "non-disagg. baseline does not exist."
            )

    service_url = f"{args.service_url}/v1"

    if not check_vllm_server(health_check_url):
        raise RuntimeError(f"vllm server: {args.service_url} is not ready yet!")

    output_strs = dict()
    for i, prompt in enumerate(SAMPLE_PROMPTS):
        use_chat_endpoint = i % 2 == 1
        output_str = run_simple_prompt(
            base_url=service_url,
            model_name=args.model_name,
            input_prompt=prompt,
            use_chat_endpoint=use_chat_endpoint,
        )
        print(f"Prompt: {prompt}, output: {output_str}")
        output_strs[prompt] = output_str

    if args.mode == "baseline":
        # baseline: save outputs
        try:
            with open(args.file_name, "w") as json_file:
                json.dump(output_strs, json_file, indent=4)
        except OSError as e:
            print(f"Error writing to file: {e}")
            raise
    else:
        # disagg. verify outputs
        baseline_outputs = None
        try:
            with open(args.file_name) as json_file:
                baseline_outputs = json.load(json_file)
        except OSError as e:
            print(f"Error writing to file: {e}")
            raise
        assert isinstance(baseline_outputs, dict)
        assert len(baseline_outputs) == len(output_strs)
        for prompt, output in baseline_outputs.items():
            assert prompt in output_strs, f"{prompt} not included"
            assert output == output_strs[prompt], (
                f"baseline_output: {output} != PD output: {output_strs[prompt]}"
            )
def parse_input_json_file(conf: dict) -> GenConvArgs:
    # Validate the input file
    assert isinstance(conf, dict)
    required_fields = [
        "filetype",
        "num_conversations",
        "text_files",
        "prompt_input",
        "prompt_output",
    ]
    for field in required_fields:
        assert field in conf, f"Missing field {field} in input {conf}"

    assert conf["filetype"] == "generate_conversations"

    assert conf["num_conversations"] > 0, "num_conversations should be larger than zero"

    text_files = conf["text_files"]

    assert isinstance(text_files, list), "Field 'text_files' should be a list"
    assert len(text_files) > 0, (
        "Field 'text_files' should be a list with at least one file"
    )

    # Parse the parameters for the prompt input/output workload
    input_num_turns = get_random_distribution(conf, "prompt_input", "num_turns")
    input_num_tokens = get_random_distribution(conf, "prompt_input", "num_tokens")
    input_common_prefix_num_tokens = get_random_distribution(
        conf, "prompt_input", "common_prefix_num_tokens", optional=True
    )
    input_prefix_num_tokens = get_random_distribution(
        conf, "prompt_input", "prefix_num_tokens"
    )
    output_num_tokens = get_random_distribution(conf, "prompt_output", "num_tokens")

    print_stats: bool = conf.get("print_stats", False)
    assert isinstance(print_stats, bool), (
        "Field 'print_stats' should be either 'true' or 'false'"
    )

    args = GenConvArgs(
        num_conversations=conf["num_conversations"],
        text_files=text_files,
        input_num_turns=input_num_turns,
        input_common_prefix_num_tokens=input_common_prefix_num_tokens,
        input_prefix_num_tokens=input_prefix_num_tokens,
        input_num_tokens=input_num_tokens,
        output_num_tokens=output_num_tokens,
        print_stats=print_stats,
    )
    return args
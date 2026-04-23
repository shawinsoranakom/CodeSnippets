def sample_requests(
    tokenizer: PreTrainedTokenizerBase, args: argparse.Namespace
) -> list[SampleRequest]:
    if args.dataset == "json" or args.dataset == "json-unique":
        if args.json_schema_path is None:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            args.json_schema_path = os.path.join(
                dir_path, "structured_schemas", "structured_schema_1.json"
            )
        json_schemas = []
        with open(args.json_schema_path) as f:
            schema = json.load(f)

        if args.dataset == "json-unique":
            json_schemas = [copy.deepcopy(schema) for _ in range(args.num_prompts)]
            for i in range(len(json_schemas)):
                if "properties" not in json_schemas[i]:
                    json_schemas[i]["properties"] = {}
                json_schemas[i]["properties"][f"__optional_field_{uuid.uuid4()}"] = {
                    "type": "string",
                    "description": "An unique optional field to avoid cached schemas",
                }
        else:
            json_schemas = [schema] * args.num_prompts

        def gen_prompt(index: int):
            return f"Generate an example of a brief user profile given the following schema: {json.dumps(get_schema(index))}"  # noqa: E501

        def get_schema(index: int):
            return json_schemas[index % len(json_schemas)]

        requests = [
            SampleRequest(
                prompt=gen_prompt(i),
                prompt_len=len(tokenizer(gen_prompt(i)).input_ids),
                expected_output_len=args.output_len,
                schema=get_schema(i),
                structure_type=args.structure_type,
            )
            for i in range(args.num_prompts)
        ]

    elif args.dataset == "grammar":
        schema = """
        root ::= select_statement

        select_statement ::= "SELECT " column " from " table " where " condition

        column ::= "col_1 " | "col_2 "

        table ::= "table_1 " | "table_2 "

        condition ::= column "= " number

        number ::= "1 " | "2 "
        """
        prompt = "Generate an SQL query to show the 'username' \
            and 'email' from the 'users' table."

        input_len = len(tokenizer(prompt).input_ids)
        print(f"Input length of the prompt: {input_len} tokens")
        requests = [
            SampleRequest(
                prompt=prompt,
                prompt_len=input_len,
                expected_output_len=args.output_len,
                schema=schema,
                structure_type=args.structure_type,
            )
            for _ in range(args.num_prompts)
        ]

    elif args.dataset == "regex":
        regex = r"\w+@\w+\.com\n"
        args.regex = regex
        prompt = "Generate an email address for Alan Turing, \
            who works in Enigma. End in .com and new line. \
                Example result: alan.turing@enigma.com\n"

        input_len = len(tokenizer(prompt).input_ids)
        print(f"Input length of the prompt: {input_len} tokens")
        requests = [
            SampleRequest(
                prompt=prompt,
                prompt_len=input_len,
                expected_output_len=args.output_len,
                schema=regex,
                structure_type=args.structure_type,
            )
            for _ in range(args.num_prompts)
        ]

    elif args.dataset == "choice":
        choice = ["Positive", "Negative"]
        args.choice = choice
        prompt = "Classify this sentiment: vLLM is wonderful!"
        input_len = len(tokenizer(prompt).input_ids)
        print(f"Input length of the prompt: {input_len} tokens")
        requests = [
            SampleRequest(
                prompt=prompt,
                prompt_len=input_len,
                expected_output_len=args.output_len,
                schema=choice,
                structure_type=args.structure_type,
            )
            for _ in range(args.num_prompts)
        ]

    elif args.dataset == "xgrammar_bench":
        requests: list[SampleRequest] = []
        dataset = datasets.load_dataset("NousResearch/json-mode-eval", split="train")
        full_dataset_len = len(dataset)

        def _filter_func(item):
            import json

            schema = json.loads(item["schema"])
            return not has_xgrammar_unsupported_json_features(schema)

        dataset = dataset.filter(_filter_func)
        num_filtered_out = full_dataset_len - len(dataset)
        print(
            f"dataset has {len(dataset)} entries after filtering "
            f"out {num_filtered_out} entries with unsupported features"
        )
        len_dataset = len(dataset)
        for data_point_idx in range(args.num_prompts):
            idx = data_point_idx
            while idx >= len_dataset:
                idx -= len_dataset
            schema = dataset["schema"][idx]
            prompt = tokenizer.apply_chat_template(
                dataset["prompt"][idx], tokenize=False, add_generation_prompt=True
            )
            input_len = len(tokenizer(prompt).input_ids)
            completion = dataset["completion"][idx]

            requests.append(
                SampleRequest(
                    prompt=prompt,
                    prompt_len=input_len,
                    expected_output_len=args.output_len,
                    schema=schema,
                    structure_type=args.structure_type,
                    completion=completion,
                )
            )

    return requests
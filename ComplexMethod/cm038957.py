def convert_sharegpt_to_openai(
    seed: int,
    input_file: str,
    output_file: str,
    max_items: int | None,
    min_content_len: int | None = None,
    max_content_len: int | None = None,
    min_turns: int | None = None,
    max_turns: int | None = None,
    model: str | None = None,
) -> None:
    if min_turns and max_turns:
        assert min_turns <= max_turns

    if min_content_len and max_content_len:
        # Verify that min is not larger than max if both were given
        assert min_content_len <= max_content_len

    print(
        f"Input parameters:\n{seed=}, {max_items=}, {min_content_len=},"
        f" {max_content_len=}, {min_turns=}, {max_turns=}\n"
    )

    random.seed(seed)

    tokenizer = None
    if model is not None:
        print(f"Loading tokenizer from: {model}")
        tokenizer = AutoTokenizer.from_pretrained(model)

    # Read the ShareGPT JSON file
    print(f"Reading file: {input_file}")
    with open(input_file, encoding="utf-8") as f:
        # Should be a list of dicts
        # Each dict should have "id" (string) and "conversations" (list of dicts)
        sharegpt_data = json.load(f)

    assert isinstance(sharegpt_data, list), "Input file should contain a list of dicts"

    print(f"Total items in input file: {len(sharegpt_data):,}")

    print(f"Shuffling dataset with seed {seed}")
    random.shuffle(sharegpt_data)

    # Map conversation ID to the all the messages
    conversation_parts: dict[str, list[Any]] = {}

    for item in tqdm.tqdm(sharegpt_data):
        assert "id" in item, "Missing key 'id'"
        assert "conversations" in item, "Missing key 'conversations'"

        # Conversation ID (e.g: "hiWPlMD") and part/session (0, 1, 2, etc.)
        conv_id, _ = item["id"].split("_")
        new_turns = item["conversations"]

        if conv_id not in conversation_parts:
            # Start new conversation
            conversation_parts[conv_id] = []
        elif len(conversation_parts[conv_id]) > 0 and len(new_turns) > 0:
            prev_turns = conversation_parts[conv_id][-1]
            if prev_turns[-1]["from"] == new_turns[0]["from"]:
                new_turns = new_turns[1:]

        if len(new_turns) > 0:
            # We assume that parts are in order in the ShareGPT dataset
            conversation_parts[conv_id].append(new_turns)

    dataset: list[dict[str, Any]] = []
    for conv_id, conv_parts in conversation_parts.items():
        new_item = {"id": conv_id}

        conversations: list[dict[str, str]] = []

        # Merge all parts
        for conv_part in conv_parts:
            conversations.extend(conv_part)

        if len(conversations) > 0:
            new_item["conversations"] = conversations
            dataset.append(new_item)

    print(f"Total unique conversations (IDs) in input file: {len(dataset):,}")

    # Final output data
    final_openai_dataset: list[dict] = []

    # Filter conversations from the ShareGPT dataset and convert to OpenAI format
    for item in tqdm.tqdm(dataset):
        messages: list[dict] = []

        assert "id" in item, "Missing key 'id'"
        assert "conversations" in item, "Missing key 'conversations'"

        conv_id = item["id"]
        conversations = item["conversations"]

        if min_turns is not None and len(conversations) < min_turns:
            # Skip short conversations
            continue

        # Convert each message in the conversation, up to max_turns if specified
        for i, turn in enumerate(conversations):
            assert "from" in turn and "value" in turn, (
                f"Invalid conversation ID {conv_id} - missing 'from' or 'value'"
            )

            role = None
            turn_from = turn["from"]

            if turn_from in {"human", "user"}:
                role = "user"
            elif turn_from in {"gpt", "bing", "chatgpt", "bard"}:
                role = "assistant"
            elif turn_from == "system":
                role = "system"

            assert role is not None, (
                f"Invalid conversation ID {conv_id} - 'from'='{turn_from}' is invalid"
            )

            if i == 0 and role != "user":
                # If the first message is from assistant (gpt), skip it.
                # this happens when the conversation is a follow-up
                # to a previous conversation (from the same user).
                continue

            if max_turns is not None and i >= max_turns:
                break

            # Convert message to OpenAI format (with "role" and "content")
            content = turn["value"]
            messages.append({"role": role, "content": content})

        # Add the converted conversation to the OpenAI format
        if len(messages) > 0:
            valid_messages = True

            # First turn should always be from the user
            user_turn = True

            for m in messages:
                # Make sure that turns alternate between user and assistant
                if (user_turn and m["role"] != "user") or (
                    not user_turn and m["role"] != "assistant"
                ):
                    valid_messages = False
                    break

                user_turn = not user_turn

                content = m["content"]
                valid_messages = content_is_valid(
                    content, min_content_len, max_content_len
                )
                if not valid_messages:
                    break

            if valid_messages is True:
                final_openai_dataset.append({"id": conv_id, "messages": messages})

    assert len(final_openai_dataset) > 0, "Final number of conversations is zero"

    print_stats(final_openai_dataset)

    print_stats_again = False
    if max_items is not None and len(final_openai_dataset) > max_items:
        print(f"\n\nSampling {max_items} items from the dataset...")
        print_stats_again = True
        final_openai_dataset = random.sample(final_openai_dataset, max_items)

    if print_stats_again:
        # Print stats after the dataset changed
        print_stats(final_openai_dataset, tokenizer)

    # Write the converted data to a new JSON file
    final_size = len(final_openai_dataset)
    print(f"\nTotal conversations converted (after filtering): {final_size:,}")
    print(f"\nWriting file: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_openai_dataset, f, ensure_ascii=False, indent=2)
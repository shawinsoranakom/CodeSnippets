def generate_conversations(
    args: GenConvArgs, tokenizer: AutoTokenizer
) -> ConversationsMap:
    # Text for all user prompts
    # (text from the input text files will be appended to this line)
    base_prompt_text = "Please rewrite the following text and add more content: "
    base_prompt_token_count = len(
        tokenizer.encode(base_prompt_text, add_special_tokens=False)
    )

    logger.info(f"{Color.PURPLE}Generating conversations...{Color.RESET}")
    logger.info(args)

    list_of_tokens = []

    for filename in args.text_files:
        # Load text file that will be used to generate prompts
        with open(filename) as file:
            data = file.read()
            tokens_in_file = tokenizer.encode(data, add_special_tokens=False)
            list_of_tokens.extend(tokens_in_file)
        logger.info(
            f"Loaded {len(tokens_in_file)} tokens from file {filename}, "
            f"total tokens so far: {len(list_of_tokens)}"
        )

    conversations: ConversationsMap = {}
    conv_id = 0

    # Generate number of turns for every conversation
    turn_count: np.ndarray = args.input_num_turns.sample(args.num_conversations)

    # Turn count should be at least 2 (one user prompt and one assistant answer)
    turn_count = np.maximum(turn_count, 2)

    # Round up to an even number (every user prompt should have an answer)
    turn_count = turn_count + (turn_count % 2)

    # Generate number of prefix tokens for every conversation
    conv_prefix_tokens: np.ndarray = args.input_prefix_num_tokens.sample(
        args.num_conversations
    )

    # Used to reduce shared text between conversations
    # (jump/skip over text sections between conversations)
    base_offset = 0

    # Common prefix size for all conversations (only 1 sample required)
    common_prefix_text = ""
    common_prefix_tokens: int = args.input_common_prefix_num_tokens.sample(1)[0]
    if common_prefix_tokens > 0:
        # Using "." at the end to separate sentences
        common_prefix_text = (
            tokenizer.decode(list_of_tokens[: common_prefix_tokens - 2]) + "."
        )
        base_offset += common_prefix_tokens

    for conv_id in tqdm(
        range(args.num_conversations),
        total=args.num_conversations,
        desc="Generating conversations",
        unit="conv",
    ):
        # Generate a single conversation
        messages: MessagesList = []

        nturns = turn_count[conv_id]

        # User prompt token count per turn (with lower limit)
        input_token_count: np.ndarray = args.input_num_tokens.sample(nturns).astype(int)
        input_token_count = np.maximum(input_token_count, base_prompt_token_count)

        # Assistant answer token count per turn (with lower limit)
        output_token_count: np.ndarray = args.output_num_tokens.sample(nturns).astype(
            int
        )
        output_token_count = np.maximum(output_token_count, 1)

        user_turn = True
        for turn_id in range(nturns):
            if user_turn:
                role = "user"
                num_tokens = input_token_count[turn_id]

                # Generate the user prompt,
                # use a unique prefix (the conv_id) for each conversation
                # (to avoid shared prefix between conversations)
                content = f"{conv_id} is a nice number... "

                if len(common_prefix_text) > 0 and turn_id == 0:
                    content = common_prefix_text + content

                # Update the number of tokens left for the content
                num_tokens -= len(tokenizer.encode(content, add_special_tokens=False))

                if turn_id == 0:
                    prefix_num_tokens = conv_prefix_tokens[conv_id]
                    if prefix_num_tokens > 0:
                        # Add prefix text (context) to the first turn
                        start_offset = base_offset
                        end_offset = start_offset + prefix_num_tokens
                        assert len(list_of_tokens) > end_offset, (
                            "Not enough input text to generate "
                            f"{prefix_num_tokens} tokens for the "
                            f"prefix text ({start_offset=}, {end_offset=})"
                        )

                        content += f"{conv_id}, " + tokenizer.decode(
                            list_of_tokens[start_offset:end_offset]
                        )
                        base_offset += prefix_num_tokens

                # Add the actual user prompt/question after the prefix text
                content += base_prompt_text
                num_tokens -= base_prompt_token_count

                if num_tokens > 0:
                    # Add text from the input file (to reach the desired token count)
                    start_offset = base_offset + turn_id * input_token_count.max()
                    end_offset = start_offset + num_tokens
                    assert len(list_of_tokens) > end_offset, (
                        f"Not enough input text to generate {num_tokens} tokens "
                        f"for the prompt ({start_offset=}, {end_offset=})"
                    )

                    # Convert tokens back to text
                    content += tokenizer.decode(list_of_tokens[start_offset:end_offset])
            else:
                role = "assistant"
                # This content will not be used as input to the LLM server
                # (actual answers will be used instead).
                # Content is only required to determine the min_tokens/max_tokens
                # (inputs to the LLM server).
                num_tokens = output_token_count[turn_id]
                assert len(list_of_tokens) > num_tokens, (
                    f"Not enough input text to generate {num_tokens} "
                    "tokens for assistant content"
                )
                content = tokenizer.decode(list_of_tokens[:num_tokens])

            # Append the user/assistant message to the list of messages
            messages.append({"role": role, "content": content})
            user_turn = not user_turn

        # Add the new conversation
        conversations[f"CONV_ID_{conv_id}"] = messages

        # Increase base offset for the next conversation
        base_offset += nturns

    if args.print_stats:
        print_conv_stats(conversations, tokenizer)

    return conversations
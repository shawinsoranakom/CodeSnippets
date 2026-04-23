def print_stats(
    conversations: "list[dict[Any, Any]]", tokenizer: AutoTokenizer | None = None
) -> None:
    # Collect statistics
    stats = []

    print("\nCollecting statistics...")
    for item in tqdm.tqdm(conversations):
        # item has "id" and "messages"
        messages = item["messages"]

        user_turns = 0
        assistant_turns = 0
        user_words = 0
        assistant_words = 0
        conv_chars = 0

        user_tokens: list[int] = []
        assistant_tokens: list[int] = []

        for m in messages:
            content = m["content"]
            conv_chars += len(content)
            content_num_words = content.count(" ") + 1

            num_tokens = 0
            if tokenizer:
                num_tokens = len(tokenizer(m["content"]).input_ids)

            if m["role"] == "user":
                user_turns += 1
                user_words += content_num_words
                if tokenizer:
                    user_tokens.append(num_tokens)

            elif m["role"] == "assistant":
                assistant_turns += 1
                assistant_words += content_num_words
                if tokenizer:
                    assistant_tokens.append(num_tokens)

        # assert user_turns == assistant_turns, \
        # f"Invalid conversation ID {item['id']}"

        conv_words = user_words + assistant_words
        item_stats = {
            "user_turns": user_turns,
            "assistant_turns": assistant_turns,
            "user_words": user_words,
            "assistant_words": assistant_words,
            "conv_turns": len(messages),
            "conv_words": conv_words,
            "conv_characters": conv_chars,
        }

        if len(user_tokens) > 0:
            item_stats["user_tokens"] = int(mean(user_tokens))

        if len(assistant_tokens) > 0:
            item_stats["assistant_tokens"] = int(mean(assistant_tokens))

        stats.append(item_stats)

    print("\nStatistics:")
    percentiles = [0.25, 0.5, 0.75, 0.9, 0.99, 0.999, 0.9999]
    df = pd.DataFrame(stats)
    print(df.describe(percentiles=percentiles).transpose())
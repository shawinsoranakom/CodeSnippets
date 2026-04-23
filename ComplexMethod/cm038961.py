def conversations_list_to_dict(input_list: ShareGptConversations) -> ConversationsMap:
    conversations: ConversationsMap = {}

    for item in input_list:
        conv_id: str = item["id"]
        assert isinstance(conv_id, str)

        assert conv_id not in conversations, (
            f"Conversation ID {conv_id} found more than once in the input"
        )

        messages: MessagesList = item["messages"]
        assert isinstance(messages, list), (
            f"Conversation messages should be a list (ID: {conv_id})"
        )
        assert len(messages) > 0, f"Conversation with no messages (ID: {conv_id})"

        conversations[conv_id] = messages

    logger.info(f"Using {len(conversations)} unique conversations (IDs)")
    assert len(conversations) == len(input_list)

    # Print statistics about the selected conversations
    stats: list[dict[str, Any]] = []
    for conv_data in conversations.values():
        stats.append({"num_turns": len(conv_data)})

    print(TEXT_SEPARATOR)
    print(f"{Color.YELLOW}Conversations statistics:{Color.RESET}")
    print(TEXT_SEPARATOR)
    percentiles = [0.25, 0.5, 0.75, 0.9, 0.99, 0.999, 0.9999]
    conv_stats = pd.DataFrame(stats).describe(percentiles=percentiles)
    print(conv_stats.transpose())
    print(TEXT_SEPARATOR)

    return conversations
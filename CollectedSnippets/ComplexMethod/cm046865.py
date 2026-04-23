def to_sharegpt(
    dataset,
    merged_prompt = "",
    merged_column_name = "instruction",
    output_column_name = "output",
    remove_unused_columns = True,
    conversation_extension = 1,
    random_state = 3407,
):
    """
    Converts a dataset to ShareGPT style.
    ShareGPT requires only 1 input and 1 output field.
    This means one has to merge multiple columns into 1 for 1 input field.
    Use `conversation_extension` to increase the length of each conversation by randomnly
    selecting a few and packing them into 1.

    merged_prompt = "",                 Prompt to merge columns into 1 input
    merged_column_name = "instruction", Final column name for the input  field
    output_column_name = "output",      Final column name for the output field
    remove_unused_columns = True,
    conversation_extension = 1,         Automatically combines `conversation_extension` convos into 1
    random_state = 3407,
    """
    if "conversations" in dataset.column_names:
        convo = dataset[0]["conversations"]
        if type(convo) is list:
            raise TypeError("Unsloth: Your dataset is probably already in ShareGPT format!")

    possible_columns, final_optional_prompts = _parse_combined_prompt(merged_prompt, dataset)
    formatter = _create_formatter(possible_columns, final_optional_prompts, merged_column_name)
    dataset = dataset.map(formatter, batched = True, desc = "Merging columns")

    def __convert_to_sharegpt__(examples):
        users      = examples[merged_column_name]
        assistants = examples[output_column_name]
        if len(users) != len(assistants):
            raise ValueError(
                "Unsloth: Input and output columns must have matching batch lengths. "
                f"Got {len(users)} {merged_column_name} rows and {len(assistants)} {output_column_name} rows."
            )
        texts = [
            [
                {"from" : "human", "value" : str(user)     },
                {"from" : "gpt",   "value" : str(assistant)},
            ] \
            for user, assistant in zip(users, assistants)
        ]
        return { "conversations" : texts, }

    dataset = dataset.map(
        __convert_to_sharegpt__,
        batched = True,
        desc = "Converting to ShareGPT",
        # Remove unused columns!
        remove_columns = dataset.column_names if remove_unused_columns else None,
    )

    # Randomnly concat conversations to create a long stream!
    from datasets import concatenate_datasets
    n_extensions = max(conversation_extension-1, 0)
    if n_extensions == 0: return dataset

    dataset = dataset.rename_columns({"conversations" : "conversations0"})
    all_shuffled = [dataset]
    for j in range(1, n_extensions+1):
        shuffled = dataset.shuffle(seed = random_state+j).rename_columns({"conversations0" : f"conversations{j}"})
        all_shuffled.append(shuffled)
    dataset = concatenate_datasets(all_shuffled, axis = 1)

    # Combine them into 1
    n_extensions += 1
    conversation_columns = [f"conversations{j}" for j in range(n_extensions)]
    def __combine_conversations__(examples):
        columns = [examples[column] for column in conversation_columns]
        convos = []
        for conversations in zip(*columns):
            merged_conversation = []
            for conversation in conversations:
                merged_conversation.extend(conversation)
            convos.append(merged_conversation)
        return {"conversations" : convos}

    dataset = dataset.map(
        __combine_conversations__,
        batched = True,
        desc = "Extending conversations",
        # Remove unused columns!
        remove_columns = dataset.column_names if remove_unused_columns else None,
    )
    return dataset
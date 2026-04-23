def standardize_chat_format(
    dataset,
    tokenizer = None,
    aliases_for_system = [
        "system",
    ],
    aliases_for_user = [
        "user",
        "human",
        "input",
    ],
    aliases_for_assistant = [
        "gpt",
        "assistant",
        "output",
    ],
    batch_size = 1000,
    num_proc = None,
):
    """
    Our own standardization function that handles BOTH messages and conversations.
    Converts non-standard role names and keys to standard format.
    """
    import collections
    import itertools
    from datasets import IterableDataset

    # Check if vision tokenizer is used
    is_vlm = False
    if tokenizer is not None:
        if hasattr(tokenizer, "image_processor") or hasattr(tokenizer, "tokenizer"):
            is_vlm = True

    column_names = set(next(iter(dataset)).keys())

    #   Check for both 'conversations' and 'messages'
    chat_column = None
    if "conversations" in column_names:
        chat_column = "conversations"
    elif "messages" in column_names:
        chat_column = "messages"
    elif "texts" in column_names:
        chat_column = "texts"
    else:
        return dataset  # No chat column found

    # Inspect structure
    examples = itertools.islice(dataset, 10)
    uniques = collections.defaultdict(list)
    for example in examples:
        for message in example[chat_column]:
            for key, value in message.items():
                if type(value) is not str:
                    continue  # Skip non-string values
                uniques[key].append(value)

    if len(uniques.keys()) != 2:
        return dataset  # Unexpected structure

    keys = list(uniques.keys())
    length_first = len(set(uniques[keys[0]]))
    length_second = len(set(uniques[keys[1]]))

    # Determine which is role and which is content
    if length_first < length_second:
        role_key = keys[0]
        content_key = keys[1]
    else:
        role_key = keys[1]
        content_key = keys[0]

    # Mapping for aliases
    aliases_mapping = {}
    for x in aliases_for_system:
        aliases_mapping[x] = "system"
    for x in aliases_for_user:
        aliases_mapping[x] = "user"
    for x in aliases_for_assistant:
        aliases_mapping[x] = "assistant"

    def _standardize_dataset(examples):
        convos = examples[chat_column]
        all_convos = []
        for convo in convos:
            new_convo = []
            for message in convo:
                # Get original role and content
                original_role = message.get(role_key, "")
                original_content = message.get(content_key, "")

                # Map to standard role name
                standard_role = aliases_mapping.get(original_role, original_role)

                # Handle VLM format
                if is_vlm:
                    original_content = [{"type": "text", "text": original_content}]

                # Create dict with EXPLICIT ORDER
                new_message = {"role": standard_role, "content": original_content}
                new_convo.append(new_message)

            all_convos.append(new_convo)

        return {chat_column: all_convos}

    dataset_map_kwargs = {
        "batched": True,
        "batch_size": batch_size,
    }

    if not isinstance(dataset, IterableDataset):
        from utils.hardware import dataset_map_num_proc

        if num_proc is None or type(num_proc) is not int:
            num_proc = dataset_map_num_proc()
        else:
            num_proc = dataset_map_num_proc(num_proc)

        dataset_map_kwargs["num_proc"] = num_proc
        dataset_map_kwargs["desc"] = "Standardizing chat format"

    return dataset.map(_standardize_dataset, **dataset_map_kwargs)
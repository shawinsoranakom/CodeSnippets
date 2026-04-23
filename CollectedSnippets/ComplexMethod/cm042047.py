def count_message_tokens(messages, model="gpt-3.5-turbo-0125"):
    """Return the number of tokens used by a list of messages."""
    if "claude" in model:
        num_tokens = count_claude_message_tokens(messages, model)
        return num_tokens
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        logger.info(f"Warning: model {model} not found in tiktoken. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-35-turbo",
        "gpt-35-turbo-16k",
        "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-1106",
        "gpt-3.5-turbo-0125",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-4-0125-preview",
        "gpt-4-1106-preview",
        "gpt-4-turbo",
        "gpt-4-vision-preview",
        "gpt-4-1106-vision-preview",
        "gpt-4o",
        "gpt-4o-2024-05-13",
        "gpt-4o-2024-08-06",
        "gpt-4o-mini",
        "gpt-4o-mini-2024-07-18",
        "o1-preview",
        "o1-preview-2024-09-12",
        "o1-mini",
        "o1-mini-2024-09-12",
    }:
        tokens_per_message = 3  # # every reply is primed with <|start|>assistant<|message|>
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" == model:
        logger.info("Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0125.")
        return count_message_tokens(messages, model="gpt-3.5-turbo-0125")
    elif "gpt-4" == model:
        logger.info("Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613.")
        return count_message_tokens(messages, model="gpt-4-0613")
    elif "open-llm-model" == model:
        """
        For self-hosted open_llm api, they include lots of different models. The message tokens calculation is
        inaccurate. It's a reference result.
        """
        tokens_per_message = 0  # ignore conversation message template prefix
        tokens_per_name = 0
    else:
        raise NotImplementedError(
            f"num_tokens_from_messages() is not implemented for model {model}. "
            f"See https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken "
            f"for information on how messages are converted to tokens."
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            content = value
            if isinstance(value, list):
                # for gpt-4v
                for item in value:
                    if isinstance(item, dict) and item.get("type") in ["text"]:
                        content = item.get("text", "")
            num_tokens += len(encoding.encode(content))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens
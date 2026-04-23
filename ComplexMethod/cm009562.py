def _first_max_tokens(
    messages: Sequence[BaseMessage],
    *,
    max_tokens: int,
    token_counter: Callable[[list[BaseMessage]], int],
    text_splitter: Callable[[str], list[str]],
    partial_strategy: Literal["first", "last"] | None = None,
    end_on: str | type[BaseMessage] | Sequence[str | type[BaseMessage]] | None = None,
) -> list[BaseMessage]:
    messages = list(messages)
    if not messages:
        return messages

    # Check if all messages already fit within token limit
    if token_counter(messages) <= max_tokens:
        # When all messages fit, only apply end_on filtering if needed
        if end_on:
            for _ in range(len(messages)):
                if not _is_message_type(messages[-1], end_on):
                    messages.pop()
                else:
                    break
        return messages

    # Use binary search to find the maximum number of messages within token limit
    left, right = 0, len(messages)
    max_iterations = len(messages).bit_length()
    for _ in range(max_iterations):
        if left >= right:
            break
        mid = (left + right + 1) // 2
        if token_counter(messages[:mid]) <= max_tokens:
            left = mid
            idx = mid
        else:
            right = mid - 1

    # idx now contains the maximum number of complete messages we can include
    idx = left

    if partial_strategy and idx < len(messages):
        included_partial = False
        copied = False
        if isinstance(messages[idx].content, list):
            excluded = messages[idx].model_copy(deep=True)
            copied = True
            num_block = len(excluded.content)
            if partial_strategy == "last":
                excluded.content = list(reversed(excluded.content))
            for _ in range(1, num_block):
                excluded.content = excluded.content[:-1]
                if token_counter([*messages[:idx], excluded]) <= max_tokens:
                    messages = [*messages[:idx], excluded]
                    idx += 1
                    included_partial = True
                    break
            if included_partial and partial_strategy == "last":
                excluded.content = list(reversed(excluded.content))
        if not included_partial:
            if not copied:
                excluded = messages[idx].model_copy(deep=True)
                copied = True

            # Extract text content efficiently
            text = None
            if isinstance(excluded.content, str):
                text = excluded.content
            elif isinstance(excluded.content, list) and excluded.content:
                for block in excluded.content:
                    if isinstance(block, str):
                        text = block
                        break
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text")
                        break

            if text:
                if not copied:
                    excluded = excluded.model_copy(deep=True)

                split_texts = text_splitter(text)
                base_message_count = token_counter(messages[:idx])
                if partial_strategy == "last":
                    split_texts = list(reversed(split_texts))

                # Binary search for the maximum number of splits we can include
                left, right = 0, len(split_texts)
                max_iterations = len(split_texts).bit_length()
                for _ in range(max_iterations):
                    if left >= right:
                        break
                    mid = (left + right + 1) // 2
                    excluded.content = "".join(split_texts[:mid])
                    if base_message_count + token_counter([excluded]) <= max_tokens:
                        left = mid
                    else:
                        right = mid - 1

                if left > 0:
                    content_splits = split_texts[:left]
                    if partial_strategy == "last":
                        content_splits = list(reversed(content_splits))
                    excluded.content = "".join(content_splits)
                    messages = [*messages[:idx], excluded]
                    idx += 1

    if end_on:
        for _ in range(idx):
            if idx > 0 and not _is_message_type(messages[idx - 1], end_on):
                idx -= 1
            else:
                break

    return messages[:idx]
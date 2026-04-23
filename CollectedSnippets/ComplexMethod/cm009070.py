def _process_batched_chunked_embeddings(
    num_texts: int,
    tokens: list[list[int] | str],
    batched_embeddings: list[list[float]],
    indices: list[int],
    skip_empty: bool,
) -> list[list[float] | None]:
    # for each text, this is the list of embeddings (list of list of floats)
    # corresponding to the chunks of the text
    results: list[list[list[float]]] = [[] for _ in range(num_texts)]

    # for each text, this is the token length of each chunk
    # for transformers tokenization, this is the string length
    # for tiktoken, this is the number of tokens
    num_tokens_in_batch: list[list[int]] = [[] for _ in range(num_texts)]

    for i in range(len(indices)):
        if skip_empty and len(batched_embeddings[i]) == 1:
            continue
        results[indices[i]].append(batched_embeddings[i])
        num_tokens_in_batch[indices[i]].append(len(tokens[i]))

    # for each text, this is the final embedding
    embeddings: list[list[float] | None] = []
    for i in range(num_texts):
        # an embedding for each chunk
        _result: list[list[float]] = results[i]

        if len(_result) == 0:
            # this will be populated with the embedding of an empty string
            # in the sync or async code calling this
            embeddings.append(None)
            continue

        if len(_result) == 1:
            # if only one embedding was produced, use it
            embeddings.append(_result[0])
            continue

        # else we need to weighted average
        # should be same as
        # average = np.average(_result, axis=0, weights=num_tokens_in_batch[i])
        total_weight = sum(num_tokens_in_batch[i])
        average = [
            sum(
                val * weight
                for val, weight in zip(embedding, num_tokens_in_batch[i], strict=False)
            )
            / total_weight
            for embedding in zip(*_result, strict=False)
        ]

        # should be same as
        # embeddings.append((average / np.linalg.norm(average)).tolist())
        magnitude = sum(val**2 for val in average) ** 0.5
        embeddings.append([val / magnitude for val in average])

    return embeddings
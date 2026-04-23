def print_tokens(target: List[int], others: List[List[int]]):
    """
    ### Print tokens

    Pretty prints tokens for comparison

    :param target: are the target token ids
    :param others: are the sampled outputs from the model(s)
    """

    # Load tokenizer
    global _TOKENIZER
    if _TOKENIZER is None:
        _TOKENIZER = get_tokenizer()

    # Convert the tokens to list of strings
    text = []
    for i in range(len(target)):
        tokens = [_TOKENIZER.decode([target[i]]) if target[i] != -1 else '---']
        for j in range(len(others)):
            tokens.append(_TOKENIZER.decode([others[j][i]]) if others[j][i] != -1 else '---')

        text.append(tokens)

    # Stats
    correct = [0 for _ in others]
    total = 0

    # Iterate through tokens
    for i in range(len(target)):
        parts = [(f'{i}: ', Text.meta)]
        parts += [('"', Text.subtle), (text[i][0], Text.subtle), ('"', Text.subtle), '\t']

        # Empty target
        if target[i] == -1:
            for j in range(len(others)):
                parts += [('"', Text.subtle), (text[i][j + 1], Text.subtle), ('"', Text.subtle), '\t']

            logger.log(parts)
            continue

        # Number of tokens
        total += 1

        # Other outputs
        for j in range(len(others)):
            correct[j] += 1 if others[j][i] == target[i] else 0

            parts += [('"', Text.subtle),
                      (text[i][j + 1], Text.success if others[j][i] == target[i] else Text.danger),
                      ('"', Text.subtle), '\t']

        logger.log(parts)

    # Stats
    parts = [(f'{total}', Text.highlight), '\t']
    for j in range(len(others)):
        parts += [(f'{correct[j]}', Text.value), '\t']
    logger.log(parts)
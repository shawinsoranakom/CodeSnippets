def generate_merges(vocab, vocab_scores: dict[str, float] | None = None, skip_tokens: Collection[str] | None = None):
    skip_tokens = set(skip_tokens) if skip_tokens is not None else set()
    reverse = vocab_scores is not None
    vocab_scores = dict(vocab_scores) if reverse else vocab

    merges = []
    for merge, piece_score in vocab_scores.items():
        if merge in skip_tokens:
            continue
        local = []
        for index in range(1, len(merge)):
            piece_l, piece_r = merge[:index], merge[index:]
            if piece_l in skip_tokens or piece_r in skip_tokens:
                continue
            if piece_l in vocab and piece_r in vocab:
                local.append((piece_l, piece_r, piece_score))
        local = sorted(local, key=lambda x: (vocab[x[0]], vocab[x[1]]))
        merges.extend(local)

    merges = sorted(merges, key=lambda val: (val[2], len(val[0]), len(val[1])), reverse=reverse)
    merges = [(val[0], val[1]) for val in merges]
    return merges
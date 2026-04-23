def _take_sentences(text, need_tokens, from_end=False):
    # Take text from one side until the target token budget is reached.
    split_pat = r"([。!?？；！\n]|\. )"
    texts = re.split(split_pat, text or "", flags=re.DOTALL)
    sentences = []
    for i in range(0, len(texts), 2):
        sentences.append(texts[i] + (texts[i + 1] if i + 1 < len(texts) else ""))
    iterator = reversed(sentences) if from_end else sentences
    collected = ""
    for sentence in iterator:
        collected = sentence + collected if from_end else collected + sentence
        if num_tokens_from_string(collected) >= need_tokens:
            break
    return collected
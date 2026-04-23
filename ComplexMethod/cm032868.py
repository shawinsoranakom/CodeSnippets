def trim_to_tokens(text, token_budget, from_tail=False):
        if token_budget <= 0 or not text:
            return ""
        sentences = split_sentences(text)
        if not sentences:
            return ""

        collected = []
        remaining = token_budget
        seq = reversed(sentences) if from_tail else sentences
        for s in seq:
            tks = num_tokens_from_string(s)
            if tks <= 0:
                continue
            if tks > remaining:
                collected.append(s)
                break
            collected.append(s)
            remaining -= tks

        if from_tail:
            collected = list(reversed(collected))
        return "".join(collected)
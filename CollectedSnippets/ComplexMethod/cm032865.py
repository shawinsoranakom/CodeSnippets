def _add_context(cks, idx, context_size):
    if cks[idx]["ck_type"] not in ("image", "table"):
        return

    prev = idx - 1
    after = idx + 1
    remain_above = context_size
    remain_below = context_size

    cks[idx]["context_above"] = ""
    cks[idx]["context_below"] = ""

    split_pat = r"([。!?？；！\n]|\. )"

    picked_above = []
    picked_below = []

    def take_sentences_from_end(cnt, need_tokens):
        txts = re.split(split_pat, cnt, flags=re.DOTALL)
        sents = []
        for j in range(0, len(txts), 2):
            sents.append(txts[j] + (txts[j + 1] if j + 1 < len(txts) else ""))
        acc = ""
        for s in reversed(sents):
            acc = s + acc
            if num_tokens_from_string(acc) >= need_tokens:
                break
        return acc

    def take_sentences_from_start(cnt, need_tokens):
        txts = re.split(split_pat, cnt, flags=re.DOTALL)
        acc = ""
        for j in range(0, len(txts), 2):
            acc += txts[j] + (txts[j + 1] if j + 1 < len(txts) else "")
            if num_tokens_from_string(acc) >= need_tokens:
                break
        return acc

    # above
    parts_above = []
    while prev >= 0 and remain_above > 0:
        if cks[prev]["ck_type"] == "text":
            tk = cks[prev]["tk_nums"]
            if tk >= remain_above:
                piece = take_sentences_from_end(cks[prev]["text"], remain_above)
                parts_above.insert(0, piece)
                picked_above.append((prev, "tail", remain_above, tk, piece[:80]))
                remain_above = 0
                break
            else:
                parts_above.insert(0, cks[prev]["text"])
                picked_above.append((prev, "full", remain_above, tk, (cks[prev]["text"] or "")[:80]))
                remain_above -= tk
        prev -= 1

    # below
    parts_below = []
    while after < len(cks) and remain_below > 0:
        if cks[after]["ck_type"] == "text":
            tk = cks[after]["tk_nums"]
            if tk >= remain_below:
                piece = take_sentences_from_start(cks[after]["text"], remain_below)
                parts_below.append(piece)
                picked_below.append((after, "head", remain_below, tk, piece[:80]))
                remain_below = 0
                break
            else:
                parts_below.append(cks[after]["text"])
                picked_below.append((after, "full", remain_below, tk, (cks[after]["text"] or "")[:80]))
                remain_below -= tk
        after += 1

    cks[idx]["context_above"] = "".join(parts_above) if parts_above else ""
    cks[idx]["context_below"] = "".join(parts_below) if parts_below else ""
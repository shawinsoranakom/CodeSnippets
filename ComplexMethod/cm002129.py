def check_details(
    line: str, spm_ids: list[int], tok_ids: list[int], slow: PreTrainedTokenizerBase, fast: PreTrainedTokenizerBase
) -> bool:
    # Encoding can be the same with same result AAA -> A + AA vs AA + A
    # We can check that we use at least exactly the same number of tokens.
    for i, (spm_id, tok_id) in enumerate(zip(spm_ids, tok_ids)):
        if spm_id != tok_id:
            break
    first = i
    for i, (spm_id, tok_id) in enumerate(zip(reversed(spm_ids), reversed(tok_ids))):
        if spm_id != tok_id:
            break
    last = len(spm_ids) - i

    spm_diff = spm_ids[first:last]
    tok_diff = tok_ids[first:last]

    if check_diff(spm_diff, tok_diff, slow, fast):
        return True

    if check_LTR_mark(line, first, fast):
        return True

    if last - first > 5:
        # We might have twice a single problem, attempt to subdivide the disjointed tokens into smaller problems
        spms = Counter(spm_ids[first:last])
        toks = Counter(tok_ids[first:last])

        removable_tokens = {spm_ for (spm_, si) in spms.items() if toks.get(spm_, 0) == si}
        min_width = 3
        for i in range(last - first - min_width):
            if all(spm_ids[first + i + j] in removable_tokens for j in range(min_width)):
                possible_matches = [
                    k
                    for k in range(last - first - min_width)
                    if tok_ids[first + k : first + k + min_width] == spm_ids[first + i : first + i + min_width]
                ]
                for j in possible_matches:
                    if check_diff(
                        spm_ids[first : first + i], tok_ids[first : first + j], slow, fast
                    ) and check_details(
                        line,
                        spm_ids[first + i : last],
                        tok_ids[first + j : last],
                        slow,
                        fast,
                    ):
                        return True

    print(f"Spm: {[fast.decode([spm_ids[i]]) for i in range(first, last)]}")
    try:
        print(f"Tok: {[fast.decode([tok_ids[i]]) for i in range(first, last)]}")
    except Exception as e:
        print(f"Could not decode tok_ids: {e}")

    fast.decode(spm_ids[:first])
    fast.decode(spm_ids[last:])
    wrong = fast.decode(spm_ids[first:last])
    print()
    print(wrong)
    return False
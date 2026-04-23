def check_LTR_mark(line: str, idx: int, fast: PreTrainedTokenizerBase) -> bool:
    enc = fast.encode_plus(line)[0]
    offsets = enc.offsets
    curr, prev = offsets[idx], offsets[idx - 1]
    if curr is not None and line[curr[0] : curr[1]] == "\u200f":
        return True
    if prev is not None and line[prev[0] : prev[1]] == "\u200f":
        return True
    return False

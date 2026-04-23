def _merge_text_chunks_by_token_size(chunks, chunk_token_size, overlapped_percent):
    # Merge adjacent text chunks when delimiter-based splitting is not active.
    merged = []
    prev_text_idx = -1
    threshold = chunk_token_size * (100 - overlapped_percent) / 100.0

    for chunk in chunks:
        if chunk["ck_type"] != "text":
            merged.append(deepcopy(chunk))
            prev_text_idx = -1
            continue

        current = deepcopy(chunk)
        should_start_new = prev_text_idx < 0 or merged[prev_text_idx]["tk_nums"] > threshold
        if should_start_new:
            if prev_text_idx >= 0 and overlapped_percent > 0 and merged[prev_text_idx]["text"]:
                overlapped = merged[prev_text_idx]["text"]
                overlap_start = int(len(overlapped) * (100 - overlapped_percent) / 100.0)
                current["text"] = overlapped[overlap_start:] + current["text"]
                current["tk_nums"] = num_tokens_from_string(current["text"])
            merged.append(current)
            prev_text_idx = len(merged) - 1
            continue

        if merged[prev_text_idx]["text"] and current["text"]:
            merged[prev_text_idx]["text"] += "\n" + current["text"]
        else:
            merged[prev_text_idx]["text"] += current["text"]
        merged[prev_text_idx][PDF_POSITIONS_KEY].extend(current.get(PDF_POSITIONS_KEY) or [])
        merged[prev_text_idx]["tk_nums"] += current["tk_nums"]

    return merged
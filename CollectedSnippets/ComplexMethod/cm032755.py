def _attach_context_to_media_chunks(chunks, table_context_size, image_context_size):
    # Add surrounding text to table/image chunks when context windows are enabled.
    for i, chunk in enumerate(chunks):
        if chunk["ck_type"] not in {"table", "image"}:
            continue

        context_size = image_context_size if chunk["ck_type"] == "image" else table_context_size
        if context_size <= 0:
            continue

        remain_above = context_size
        remain_below = context_size
        parts_above = []
        parts_below = []

        prev = i - 1
        while prev >= 0 and remain_above > 0:
            prev_chunk = chunks[prev]
            if prev_chunk["ck_type"] == "text":
                if prev_chunk["tk_nums"] >= remain_above:
                    parts_above.insert(0, _take_sentences(prev_chunk["text"], remain_above, from_end=True))
                    remain_above = 0
                    break
                parts_above.insert(0, prev_chunk["text"])
                remain_above -= prev_chunk["tk_nums"]
            prev -= 1

        after = i + 1
        while after < len(chunks) and remain_below > 0:
            after_chunk = chunks[after]
            if after_chunk["ck_type"] == "text":
                if after_chunk["tk_nums"] >= remain_below:
                    parts_below.append(_take_sentences(after_chunk["text"], remain_below))
                    remain_below = 0
                    break
                parts_below.append(after_chunk["text"])
                remain_below -= after_chunk["tk_nums"]
            after += 1

        chunk["context_above"] = "".join(parts_above)
        chunk["context_below"] = "".join(parts_below)
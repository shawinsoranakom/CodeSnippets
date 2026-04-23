def _merge_cks(cks, chunk_token_num, has_custom):
    merged = []
    image_idxs = []
    prev_text_ck = -1

    for i in range(len(cks)):
        ck_type = cks[i]["ck_type"]

        if ck_type != "text":
            merged.append(cks[i])
            if ck_type == "image":
                image_idxs.append(len(merged) - 1)
            continue

        if prev_text_ck<0 or merged[prev_text_ck]["tk_nums"] >= chunk_token_num or has_custom:
            merged.append(cks[i])
            prev_text_ck = len(merged) - 1
            continue

        merged[prev_text_ck]["text"] = (merged[prev_text_ck].get("text") or "") + (cks[i].get("text") or "")
        merged[prev_text_ck]["tk_nums"] = merged[prev_text_ck].get("tk_nums", 0) + cks[i].get("tk_nums", 0)

    return merged, image_idxs
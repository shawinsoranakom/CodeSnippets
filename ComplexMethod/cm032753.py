def _build_json_chunks(json_result, delimiter_pattern):
    # Convert upstream JSON items into internal working chunks.
    chunks = []
    for item in json_result:
        doc_type = str(item.get("doc_type_kwd") or "").strip().lower()
        if doc_type == "table":
            ck_type = "table"
        elif doc_type == "image":
            ck_type = "image"
        else:
            ck_type = "text"

        text = item.get("text")
        if not isinstance(text, str):
            text = item.get("content_with_weight")
        if not isinstance(text, str):
            text = ""

        # Keep PDF coordinates as an internal preview field until the final
        # output is assembled. This avoids leaking two public coordinate
        # formats downstream.
        preview_positions = extract_pdf_positions(item)
        img_id = item.get("img_id")

        if ck_type == "text":
            text_segments = _split_text_by_pattern(text, delimiter_pattern) if delimiter_pattern else [text]
            for segment in text_segments:
                if not segment or not segment.strip():
                    continue
                chunks.append(
                    {
                        "text": segment,
                        "doc_type_kwd": "text",
                        "ck_type": "text",
                        PDF_POSITIONS_KEY: deepcopy(preview_positions),
                        "tk_nums": num_tokens_from_string(segment),
                    }
                )
            continue

        chunks.append(
            {
                "text": text or "",
                "doc_type_kwd": ck_type,
                "ck_type": ck_type,
                "img_id": img_id,
                PDF_POSITIONS_KEY: deepcopy(preview_positions),
                "tk_nums": num_tokens_from_string(text or ""),
                "context_above": "",
                "context_below": "",
            }
        )

    return chunks
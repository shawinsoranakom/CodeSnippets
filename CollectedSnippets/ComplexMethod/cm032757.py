def _finalize_json_chunks(chunks):
    # Convert internal chunks into the final token chunker output format.
    docs = []
    for chunk in chunks:
        text = (chunk.get("context_above") or "") + (chunk.get("text") or "") + (chunk.get("context_below") or "")
        if not text.strip():
            continue

        # The internal preview coordinates are converted exactly once into the
        # indexed fields consumed downstream.
        doc = {
            "text": text,
            "doc_type_kwd": chunk.get("doc_type_kwd", "text"),
        }
        if chunk.get(PDF_POSITIONS_KEY):
            doc[PDF_POSITIONS_KEY] = deepcopy(chunk[PDF_POSITIONS_KEY])
        if chunk.get("mom"):
            doc["mom"] = chunk["mom"]
        if chunk.get("img_id"):
            doc["img_id"] = chunk["img_id"]
        docs.append(finalize_pdf_chunk(doc))

    return docs
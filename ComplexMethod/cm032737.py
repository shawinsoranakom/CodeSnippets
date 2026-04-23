async def restore_pdf_text_previews(chunks, from_upstream, canvas):
    if not chunks or not str(from_upstream.name).lower().endswith(".pdf"):
        return

    text_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("doc_type_kwd", "text") == "text" and extract_pdf_positions(chunk)
    ]
    if not text_chunks:
        return

    blob = _fetch_source_blob(from_upstream, canvas)
    if not blob:
        return

    try:
        page_images = _load_pdf_page_images(blob)
    except Exception as e:
        logging.warning(f"Failed to load PDF page images for chunk preview restore: {e}")
        return

    preview_cache = {}
    storage_put = partial(settings.STORAGE_IMPL.put, tenant_id=canvas._tenant_id)
    for chunk in text_chunks:
        preview_positions = extract_pdf_positions(chunk)
        positions_key = tuple(tuple(pos[:5]) for pos in preview_positions)
        if not positions_key:
            continue
        if positions_key in preview_cache:
            chunk["img_id"] = preview_cache[positions_key]
            continue

        preview = _crop_pdf_preview(page_images, preview_positions)
        if not preview:
            continue

        chunk["image"] = preview
        await image2id(chunk, storage_put, get_uuid())
        if chunk.get("img_id"):
            preview_cache[positions_key] = chunk["img_id"]
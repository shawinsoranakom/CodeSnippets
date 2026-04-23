def _build_reference_chunks(reference, include_metadata=False, metadata_fields=None):
    chunks = chunks_format(reference)
    if not include_metadata:
        return chunks

    doc_ids_by_kb = {}
    for chunk in chunks:
        kb_id = chunk.get("dataset_id")
        doc_id = chunk.get("document_id")
        if not kb_id or not doc_id:
            continue
        doc_ids_by_kb.setdefault(kb_id, set()).add(doc_id)

    if not doc_ids_by_kb:
        return chunks

    meta_by_doc = {}
    for kb_id, doc_ids in doc_ids_by_kb.items():
        meta_map = DocMetadataService.get_metadata_for_documents(list(doc_ids), kb_id)
        if meta_map:
            meta_by_doc.update(meta_map)

    if metadata_fields is not None:
        metadata_fields = {f for f in metadata_fields if isinstance(f, str)}
        if not metadata_fields:
            return chunks

    for chunk in chunks:
        doc_id = chunk.get("document_id")
        if not doc_id:
            continue
        meta = meta_by_doc.get(doc_id)
        if not meta:
            continue
        if metadata_fields is not None:
            meta = {k: v for k, v in meta.items() if k in metadata_fields}
        if meta:
            chunk["document_metadata"] = meta

    return chunks
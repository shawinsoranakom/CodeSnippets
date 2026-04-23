async def metadata_batch_update(dataset_id, tenant_id):
    if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
        return get_error_data_result(message=f"You don't own the dataset {dataset_id}. ")

    req = await get_request_json()
    selector = req.get("selector", {}) or {}
    updates = req.get("updates", []) or []
    deletes = req.get("deletes", []) or []

    if not isinstance(selector, dict):
        return get_error_data_result(message="selector must be an object.")
    if not isinstance(updates, list) or not isinstance(deletes, list):
        return get_error_data_result(message="updates and deletes must be lists.")

    metadata_condition = selector.get("metadata_condition", {}) or {}
    if metadata_condition and not isinstance(metadata_condition, dict):
        return get_error_data_result(message="metadata_condition must be an object.")

    document_ids = selector.get("document_ids", []) or []
    if document_ids and not isinstance(document_ids, list):
        return get_error_data_result(message="document_ids must be a list.")

    for upd in updates:
        if not isinstance(upd, dict) or not upd.get("key") or "value" not in upd:
            return get_error_data_result(message="Each update requires key and value.")
    for d in deletes:
        if not isinstance(d, dict) or not d.get("key"):
            return get_error_data_result(message="Each delete requires key.")

    if document_ids:
        kb_doc_ids = KnowledgebaseService.list_documents_by_ids([dataset_id])
        target_doc_ids = set(kb_doc_ids)
        invalid_ids = set(document_ids) - set(kb_doc_ids)
        if invalid_ids:
            return get_error_data_result(message=f"These documents do not belong to dataset {dataset_id}: {', '.join(invalid_ids)}")
        target_doc_ids = set(document_ids)

    if metadata_condition:
        metas = DocMetadataService.get_flatted_meta_by_kbs([dataset_id])
        filtered_ids = set(meta_filter(metas, convert_conditions(metadata_condition), metadata_condition.get("logic", "and")))
        target_doc_ids = target_doc_ids & filtered_ids
        if metadata_condition.get("conditions") and not target_doc_ids:
            return get_result(data={"updated": 0, "matched_docs": 0})

    target_doc_ids = list(target_doc_ids)
    updated = DocMetadataService.batch_update_metadata(dataset_id, target_doc_ids, updates, deletes)
    return get_result(data={"updated": updated, "matched_docs": len(target_doc_ids)})
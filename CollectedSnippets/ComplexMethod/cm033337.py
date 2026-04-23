async def metadata_update():
    req = await get_request_json()
    kb_id = req.get("kb_id")
    document_ids = req.get("doc_ids")
    updates = req.get("updates", []) or []
    deletes = req.get("deletes", []) or []

    if not kb_id:
        return get_json_result(data=False, message='Lack of "KB ID"', code=RetCode.ARGUMENT_ERROR)

    if not isinstance(updates, list) or not isinstance(deletes, list):
        return get_json_result(data=False, message="updates and deletes must be lists.", code=RetCode.ARGUMENT_ERROR)

    for upd in updates:
        if not isinstance(upd, dict) or not upd.get("key") or "value" not in upd:
            return get_json_result(data=False, message="Each update requires key and value.", code=RetCode.ARGUMENT_ERROR)
    for d in deletes:
        if not isinstance(d, dict) or not d.get("key"):
            return get_json_result(data=False, message="Each delete requires key.", code=RetCode.ARGUMENT_ERROR)

    updated = DocMetadataService.batch_update_metadata(kb_id, document_ids, updates, deletes)
    return get_json_result(data={"updated": updated, "matched_docs": len(document_ids)})
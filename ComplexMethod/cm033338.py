async def change_status():
    req = await get_request_json()
    doc_ids = req.get("doc_ids", [])
    status = str(req.get("status", ""))

    if status not in ["0", "1"]:
        return get_json_result(data=False, message='"Status" must be either 0 or 1!', code=RetCode.ARGUMENT_ERROR)

    result = {}
    has_error = False
    for doc_id in doc_ids:
        if not DocumentService.accessible(doc_id, current_user.id):
            result[doc_id] = {"error": "No authorization."}
            has_error = True
            continue

        try:
            e, doc = DocumentService.get_by_id(doc_id)
            if not e:
                result[doc_id] = {"error": "No authorization."}
                has_error = True
                continue
            e, kb = KnowledgebaseService.get_by_id(doc.kb_id)
            if not e:
                result[doc_id] = {"error": "Can't find this dataset!"}
                has_error = True
                continue
            current_status = str(doc.status)
            if current_status == status:
                result[doc_id] = {"status": status}
                continue
            if not DocumentService.update_by_id(doc_id, {"status": str(status)}):
                result[doc_id] = {"error": "Database error (Document update)!"}
                has_error = True
                continue

            status_int = int(status)
            if getattr(doc, "chunk_num", 0) > 0:
                try:
                    ok = settings.docStoreConn.update(
                        {"doc_id": doc_id},
                        {"available_int": status_int},
                        search.index_name(kb.tenant_id),
                        doc.kb_id,
                    )
                except Exception as exc:
                    msg = str(exc)
                    if "3022" in msg:
                        result[doc_id] = {"error": "Document store table missing."}
                    else:
                        result[doc_id] = {"error": f"Document store update failed: {msg}"}
                    has_error = True
                    continue
                if not ok:
                    result[doc_id] = {"error": "Database error (docStore update)!"}
                    has_error = True
                    continue
            result[doc_id] = {"status": status}
        except Exception as e:
            result[doc_id] = {"error": f"Internal server error: {str(e)}"}
            has_error = True

    if has_error:
        return get_json_result(data=result, message="Partial failure", code=RetCode.SERVER_ERROR)
    return get_json_result(data=result)
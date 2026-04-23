def _rm_sync():
            deleted_chunk_ids = req.get("chunk_ids")
            if isinstance(deleted_chunk_ids, list):
                unique_chunk_ids = list(dict.fromkeys(deleted_chunk_ids))
                has_ids = len(unique_chunk_ids) > 0
            elif deleted_chunk_ids is not None:
                unique_chunk_ids = [deleted_chunk_ids]
                has_ids = deleted_chunk_ids not in (None, "")
            else:
                unique_chunk_ids = []
                has_ids = False
            if not has_ids:
                if req.get("delete_all") is True:
                    e, doc = DocumentService.get_by_id(req["doc_id"])
                    if not e:
                        return get_data_error_result(message="Document not found!")
                    tenant_id = DocumentService.get_tenant_id(req["doc_id"])
                    # Clean up storage assets while index rows still exist for discovery
                    DocumentService.delete_chunk_images(doc, tenant_id)
                    condition = {"doc_id": req["doc_id"]}
                    try:
                        deleted_count = settings.docStoreConn.delete(condition, search.index_name(tenant_id), doc.kb_id)
                    except Exception:
                        return get_data_error_result(message="Chunk deleting failure")
                    if deleted_count > 0:
                        DocumentService.decrement_chunk_num(doc.id, doc.kb_id, 1, deleted_count, 0)
                    return get_json_result(data=True)
                return get_json_result(data=True)

            e, doc = DocumentService.get_by_id(req["doc_id"])
            if not e:
                return get_data_error_result(message="Document not found!")
            condition = {"id": req["chunk_ids"], "doc_id": req["doc_id"]}
            try:
                deleted_count = settings.docStoreConn.delete(condition,
                                                             search.index_name(DocumentService.get_tenant_id(req["doc_id"])),
                                                             doc.kb_id)
            except Exception:
                return get_data_error_result(message="Chunk deleting failure")
            if has_ids and deleted_count == 0:
                return get_data_error_result(message="Index updating failure")
            if deleted_count > 0 and deleted_count < len(unique_chunk_ids):
                deleted_count += settings.docStoreConn.delete({"doc_id": req["doc_id"]},
                                                              search.index_name(DocumentService.get_tenant_id(req["doc_id"])),
                                                              doc.kb_id)
            chunk_number = deleted_count
            DocumentService.decrement_chunk_num(doc.id, doc.kb_id, 1, chunk_number, 0)
            for cid in deleted_chunk_ids:
                if settings.STORAGE_IMPL.obj_exist(doc.kb_id, cid):
                    settings.STORAGE_IMPL.rm(doc.kb_id, cid)
            return get_json_result(data=True)
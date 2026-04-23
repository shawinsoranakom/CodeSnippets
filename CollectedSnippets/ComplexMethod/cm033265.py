def cleanup_stale_documents_for_task(
        cls,
        task_id: str,
        connector_id: str,
        kb_id: str,
        tenant_id: str,
        file_list,
        delete_batch_size: int = 100,
    ):
        from api.db.services.file_service import FileService

        if not Connector2KbService.query(connector_id=connector_id, kb_id=kb_id):
            return 0, []

        e, conn = cls.get_by_id(connector_id)
        if not e:
            return 0, []

        source_type = f"{conn.source}/{conn.id}"
        retain_doc_ids = {hash128(file.id) for file in file_list}
        existing_docs = DocumentService.list_doc_headers_by_kb_and_source_type(
            kb_id,
            source_type,
        )
        stale_doc_ids = [
            doc["id"] for doc in existing_docs if doc["id"] not in retain_doc_ids
        ]
        if not stale_doc_ids:
            return 0, []

        stale_doc_id_set = set(stale_doc_ids)
        errors = []
        for offset in range(0, len(stale_doc_ids), delete_batch_size):
            err = FileService.delete_docs(
                stale_doc_ids[offset : offset + delete_batch_size],
                tenant_id,
            )
            if err:
                errors.append(err)

        remaining_doc_ids = {
            doc["id"]
            for doc in DocumentService.list_doc_headers_by_kb_and_source_type(
                kb_id,
                source_type,
            )
            if doc["id"] in stale_doc_id_set
        }
        removed_count = len(stale_doc_id_set) - len(remaining_doc_ids)
        SyncLogsService.increase_removed_docs(
            task_id,
            removed_count,
            "\n".join(errors),
            len(errors),
        )
        return removed_count, errors
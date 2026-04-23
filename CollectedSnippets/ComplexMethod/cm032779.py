async def _run_task_logic(self, task: dict):
        generate_output = await self._generate(task)
        # `_generate()` currently supports two outputs:
        # 1. `document_batch_generator`
        # 2. `(document_batch_generator, file_list)`
        if isinstance(generate_output, tuple):
            document_batch_generator, file_list = generate_output
        else:
            document_batch_generator = generate_output
            file_list = None

        failed_docs = 0
        added_docs = 0
        updated_docs = 0
        removed_docs = 0
        next_update = datetime(1970, 1, 1, tzinfo=timezone.utc)
        source_type = f"{self.SOURCE_NAME}/{task['connector_id']}"
        existing_doc_ids = {
            doc["id"]
            for doc in DocumentService.list_doc_headers_by_kb_and_source_type(
                task["kb_id"],
                source_type,
            )
        }

        if task["poll_range_start"]:
            next_update = task["poll_range_start"]

        for document_batch in document_batch_generator:
            if not document_batch:
                continue

            max_update = max(doc.doc_updated_at for doc in document_batch)
            next_update = max(next_update, max_update)

            docs = []
            for doc in document_batch:
                d = {
                    "id": hash128(doc.id),
                    "connector_id": task["connector_id"],
                    "source": self.SOURCE_NAME,
                    "semantic_identifier": doc.semantic_identifier,
                    "extension": doc.extension,
                    "size_bytes": doc.size_bytes,
                    "doc_updated_at": doc.doc_updated_at,
                    "blob": doc.blob,
                }
                if doc.metadata:
                    d["metadata"] = doc.metadata
                docs.append(d)

            try:
                e, kb = KnowledgebaseService.get_by_id(task["kb_id"])
                err, dids = SyncLogsService.duplicate_and_parse(
                    kb, docs, task["tenant_id"],
                    f"{self.SOURCE_NAME}/{task['connector_id']}",
                    task["auto_parse"]
                )
                SyncLogsService.increase_docs(
                    task["id"], max_update,
                    len(docs), "\n".join(err), len(err)
                )
                changed_doc_ids = set(dids)
                updated_in_batch = len(changed_doc_ids & existing_doc_ids)
                added_in_batch = len(changed_doc_ids) - updated_in_batch
                added_docs += added_in_batch
                updated_docs += updated_in_batch
                existing_doc_ids.update(changed_doc_ids)

            except Exception as batch_ex:
                msg = str(batch_ex)
                code = getattr(batch_ex, "args", [None])[0]

                if code == 1267 or "collation" in msg.lower():
                    logging.warning(f"Skipping {len(docs)} document(s) due to collation conflict")
                else:
                    logging.error(f"Error processing batch: {msg}")

                failed_docs += len(docs)
                continue

        prefix = self._get_source_prefix()
        prefix = f"{prefix} " if prefix else ""
        next_update_info = self._format_window_boundary(next_update)
        if file_list is not None:
            removed_docs, _ = ConnectorService.cleanup_stale_documents_for_task(
                task["id"],
                task["connector_id"],
                task["kb_id"],
                task["tenant_id"],
                file_list,
            )

        total_changed_docs = added_docs + updated_docs + removed_docs
        summary = (
            f"{prefix}sync summary till {next_update_info}: "
            f"total={total_changed_docs}, added={added_docs}, "
            f"updated={updated_docs}, deleted={removed_docs}"
        )
        if failed_docs > 0:
            summary = f"{summary}, skipped={failed_docs}"
        logging.info(summary)

        SyncLogsService.done(task["id"], task["connector_id"])
        task["poll_range_start"] = next_update
def remove_document(cls, doc, tenant_id):
        from api.db.services.task_service import TaskService, cancel_all_task_of

        if not cls.delete_document_and_update_kb_counts(doc.id):
            return True

        # Cancel all running tasks first Using preset function in task_service.py ---  set cancel flag in Redis
        try:
            cancel_all_task_of(doc.id)
            logging.info(f"Cancelled all tasks for document {doc.id}")
        except Exception as e:
            logging.warning(f"Failed to cancel tasks for document {doc.id}: {e}")

        # Delete tasks from database
        try:
            TaskService.filter_delete([Task.doc_id == doc.id])
        except Exception as e:
            logging.warning(f"Failed to delete tasks for document {doc.id}: {e}")

        # Delete chunk images (non-critical, log and continue)
        try:
            cls.delete_chunk_images(doc, tenant_id)
        except Exception as e:
            logging.warning(f"Failed to delete chunk images for document {doc.id}: {e}")

        # Delete thumbnail (non-critical, log and continue)
        try:
            if doc.thumbnail and not doc.thumbnail.startswith(IMG_BASE64_PREFIX):
                if settings.STORAGE_IMPL.obj_exist(doc.kb_id, doc.thumbnail):
                    settings.STORAGE_IMPL.rm(doc.kb_id, doc.thumbnail)
        except Exception as e:
            logging.warning(f"Failed to delete thumbnail for document {doc.id}: {e}")

        # Delete chunks from doc store - this is critical, log errors
        try:
            settings.docStoreConn.delete({"doc_id": doc.id}, search.index_name(tenant_id), doc.kb_id)
        except Exception as e:
            logging.error(f"Failed to delete chunks from doc store for document {doc.id}: {e}")

        # Delete document metadata (non-critical, log and continue)
        try:
            DocMetadataService.delete_document_metadata(doc.id, doc.kb_id, tenant_id)
        except Exception as e:
            logging.warning(f"Failed to delete metadata for document {doc.id}: {e}")

        # Cleanup knowledge graph references (non-critical, log and continue)
        try:
            graph_source = settings.docStoreConn.get_fields(
                settings.docStoreConn.search(["source_id"], [], {"kb_id": doc.kb_id, "knowledge_graph_kwd": ["graph"]}, [], OrderByExpr(), 0, 1, search.index_name(tenant_id), [doc.kb_id]),
                ["source_id"],
            )
            if len(graph_source) > 0 and doc.id in list(graph_source.values())[0]["source_id"]:
                settings.docStoreConn.update(
                    {"kb_id": doc.kb_id, "knowledge_graph_kwd": ["entity", "relation", "graph", "subgraph", "community_report"], "source_id": doc.id},
                    {"remove": {"source_id": doc.id}},
                    search.index_name(tenant_id),
                    doc.kb_id,
                )
                settings.docStoreConn.update({"kb_id": doc.kb_id, "knowledge_graph_kwd": ["graph"]}, {"removed_kwd": "Y"}, search.index_name(tenant_id), doc.kb_id)
                settings.docStoreConn.delete(
                    {"kb_id": doc.kb_id, "knowledge_graph_kwd": ["entity", "relation", "graph", "subgraph", "community_report"], "must_not": {"exists": "source_id"}},
                    search.index_name(tenant_id),
                    doc.kb_id,
                )
        except Exception as e:
            logging.warning(f"Failed to cleanup knowledge graph for document {doc.id}: {e}")

        return True
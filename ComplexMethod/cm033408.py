def _convert_files(file_ids, kb_ids, user_id):
    """Synchronous worker: delete old docs and insert new ones for the given file/kb pairs."""
    for id in file_ids:
        informs = File2DocumentService.get_by_file_id(id)
        for inform in informs:
            doc_id = inform.document_id
            e, doc = DocumentService.get_by_id(doc_id)
            if not e:
                continue
            tenant_id = DocumentService.get_tenant_id(doc_id)
            if not tenant_id:
                logging.warning("tenant_id not found for doc_id=%s, skipping remove_document", doc_id)
                continue
            DocumentService.remove_document(doc, tenant_id)
        File2DocumentService.delete_by_file_id(id)

        e, file = FileService.get_by_id(id)
        if not e:
            continue

        for kb_id in kb_ids:
            e, kb = KnowledgebaseService.get_by_id(kb_id)
            if not e:
                continue
            doc = DocumentService.insert({
                "id": get_uuid(),
                "kb_id": kb.id,
                "parser_id": FileService.get_parser(file.type, file.name, kb.parser_id),
                "pipeline_id": kb.pipeline_id,
                "parser_config": kb.parser_config,
                "created_by": user_id,
                "type": file.type,
                "name": file.name,
                "suffix": Path(file.name).suffix.lstrip("."),
                "location": file.location,
                "size": file.size
            })
            File2DocumentService.insert({
                "id": get_uuid(),
                "file_id": id,
                "document_id": doc.id,
            })
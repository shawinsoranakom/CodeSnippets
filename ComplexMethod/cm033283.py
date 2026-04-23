def delete_docs(cls, doc_ids, tenant_id):
        root_folder = FileService.get_root_folder(tenant_id)
        pf_id = root_folder["id"]
        FileService.init_knowledgebase_docs(pf_id, tenant_id)
        errors = ""
        kb_table_num_map = {}
        for doc_id in doc_ids:
            try:
                e, doc = DocumentService.get_by_id(doc_id)
                if not e:
                    raise Exception("Document not found!")
                tenant_id = DocumentService.get_tenant_id(doc_id)
                if not tenant_id:
                    raise Exception("Tenant not found!")

                b, n = File2DocumentService.get_storage_address(doc_id=doc_id)

                TaskService.filter_delete([Task.doc_id == doc_id])
                if not DocumentService.remove_document(doc, tenant_id):
                    raise Exception("Database error (Document removal)!")

                f2d = File2DocumentService.get_by_document_id(doc_id)
                deleted_file_count = 0
                if f2d:
                    deleted_file_count = FileService.filter_delete([File.source_type == FileSource.KNOWLEDGEBASE, File.id == f2d[0].file_id])
                File2DocumentService.delete_by_document_id(doc_id)
                if deleted_file_count > 0:
                    settings.STORAGE_IMPL.rm(b, n)

                doc_parser = doc.parser_id
                if doc_parser == ParserType.TABLE:
                    kb_id = doc.kb_id
                    if kb_id not in kb_table_num_map:
                        counts = DocumentService.count_by_kb_id(kb_id=kb_id, keywords="", run_status=[TaskStatus.DONE], types=[])
                        kb_table_num_map[kb_id] = counts
                    kb_table_num_map[kb_id] -= 1
                    if kb_table_num_map[kb_id] <= 0:
                        KnowledgebaseService.delete_field_map(kb_id)
            except Exception as e:
                errors += str(e)

        return errors
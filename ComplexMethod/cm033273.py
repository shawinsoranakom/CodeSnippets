def get_by_kb_id(cls, kb_id, page_number, items_per_page, orderby, desc, keywords, run_status, types, suffix, name=None, doc_ids=None, return_empty_metadata=False):
        fields = cls.get_cls_model_fields()
        if keywords:
            docs = (
                cls.model.select(*[*fields, UserCanvas.title.alias("pipeline_name"), User.nickname])
                .join(File2Document, on=(File2Document.document_id == cls.model.id))
                .join(File, on=(File.id == File2Document.file_id))
                .join(UserCanvas, on=(cls.model.pipeline_id == UserCanvas.id), join_type=JOIN.LEFT_OUTER)
                .join(User, on=(cls.model.created_by == User.id), join_type=JOIN.LEFT_OUTER)
                .where((cls.model.kb_id == kb_id), (fn.LOWER(cls.model.name).contains(keywords.lower())))
            )
        else:
            docs = (
                cls.model.select(*[*fields, UserCanvas.title.alias("pipeline_name"), User.nickname])
                .join(File2Document, on=(File2Document.document_id == cls.model.id))
                .join(UserCanvas, on=(cls.model.pipeline_id == UserCanvas.id), join_type=JOIN.LEFT_OUTER)
                .join(File, on=(File.id == File2Document.file_id))
                .join(User, on=(cls.model.created_by == User.id), join_type=JOIN.LEFT_OUTER)
                .where(cls.model.kb_id == kb_id)
            )
        if doc_ids:
            docs = docs.where(cls.model.id.in_(doc_ids))
        if run_status:
            docs = docs.where(cls.model.run.in_(run_status))
        if types:
            docs = docs.where(cls.model.type.in_(types))
        if suffix:
            docs = docs.where(cls.model.suffix.in_(suffix))
        if name:
            docs = docs.where(cls.model.name == name)

        if return_empty_metadata:
            metadata_map = DocMetadataService.get_metadata_for_documents(None, kb_id)
            doc_ids_with_metadata = set(metadata_map.keys())
            if doc_ids_with_metadata:
                docs = docs.where(cls.model.id.not_in(doc_ids_with_metadata))

        count = docs.count()
        if desc:
            docs = docs.order_by(cls.model.getter_by(orderby).desc())
        else:
            docs = docs.order_by(cls.model.getter_by(orderby).asc())

        if page_number and items_per_page:
            docs = docs.paginate(page_number, items_per_page)

        docs_list = list(docs.dicts())
        if return_empty_metadata:
            for doc in docs_list:
                doc["meta_fields"] = {}
        else:
            doc_ids_on_page = [doc["id"] for doc in docs_list]
            metadata_map = DocMetadataService.get_metadata_for_documents(doc_ids_on_page, kb_id) if doc_ids_on_page else {}
            for doc in docs_list:
                doc["meta_fields"] = metadata_map.get(doc["id"], {})
        return docs_list, count
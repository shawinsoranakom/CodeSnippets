def get_list(cls, kb_id, page_number, items_per_page, orderby, desc, keywords, id, name, suffix=None, run=None, doc_ids=None):
        fields = cls.get_cls_model_fields()
        docs = (
            cls.model.select(*[*fields, UserCanvas.title])
            .join(File2Document, on=(File2Document.document_id == cls.model.id))
            .join(File, on=(File.id == File2Document.file_id))
            .join(UserCanvas, on=((cls.model.pipeline_id == UserCanvas.id) & (UserCanvas.canvas_category == CanvasCategory.DataFlow.value)), join_type=JOIN.LEFT_OUTER)
            .where(cls.model.kb_id == kb_id)
        )
        if id:
            docs = docs.where(cls.model.id == id)
        if name:
            docs = docs.where(cls.model.name == name)
        if keywords:
            docs = docs.where(fn.LOWER(cls.model.name).contains(keywords.lower()))
        if doc_ids:
            docs = docs.where(cls.model.id.in_(doc_ids))
        if suffix:
            docs = docs.where(cls.model.suffix.in_(suffix))
        if run:
            docs = docs.where(cls.model.run.in_(run))
        if desc:
            docs = docs.order_by(cls.model.getter_by(orderby).desc())
        else:
            docs = docs.order_by(cls.model.getter_by(orderby).asc())

        count = docs.count()
        docs = docs.paginate(page_number, items_per_page)

        docs_list = list(docs.dicts())
        doc_ids_on_page = [doc["id"] for doc in docs_list]
        metadata_map = DocMetadataService.get_metadata_for_documents(doc_ids_on_page, kb_id) if doc_ids_on_page else {}
        for doc in docs_list:
            doc["meta_fields"] = metadata_map.get(doc["id"], {})
        return docs_list, count
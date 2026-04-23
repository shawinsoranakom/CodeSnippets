def get_file_logs_by_kb_id(cls, kb_id, page_number, items_per_page, orderby, desc, keywords, operation_status, types, suffix, create_date_from=None, create_date_to=None):
        fields = cls.get_file_logs_fields()
        if keywords:
            logs = cls.model.select(*fields).where((cls.model.kb_id == kb_id), (fn.LOWER(cls.model.document_name).contains(keywords.lower())))
        else:
            logs = cls.model.select(*fields).where(cls.model.kb_id == kb_id)

        logs = logs.where(cls.model.document_id != GRAPH_RAPTOR_FAKE_DOC_ID)

        if operation_status:
            logs = logs.where(cls.model.operation_status.in_(operation_status))
        if types:
            logs = logs.where(cls.model.document_type.in_(types))
        if suffix:
            logs = logs.where(cls.model.document_suffix.in_(suffix))
        if create_date_from:
            logs = logs.where(cls.model.create_date >= create_date_from)
        if create_date_to:
            logs = logs.where(cls.model.create_date <= create_date_to)

        count = logs.count()
        if desc:
            logs = logs.order_by(cls.model.getter_by(orderby).desc())
        else:
            logs = logs.order_by(cls.model.getter_by(orderby).asc())

        if page_number and items_per_page:
            logs = logs.paginate(page_number, items_per_page)

        return list(logs.dicts()), count
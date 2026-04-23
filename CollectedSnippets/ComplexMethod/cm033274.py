def get_filter_by_kb_id(cls, kb_id, keywords, run_status, types, suffix):
        """
        returns:
        {
            "suffix": {
                "ppt": 1,
                "doxc": 2
            },
            "run_status": {
             "1": 2,
             "2": 2
            }
            "metadata": {
                "key1": {
                 "key1_value1": 1,
                 "key1_value2": 2,
                },
                "key2": {
                 "key2_value1": 2,
                 "key2_value2": 1,
                },
            }
        }, total
        where "1" => RUNNING, "2" => CANCEL
        """
        fields = cls.get_cls_model_fields()
        if keywords:
            query = (
                cls.model.select(*fields)
                .join(File2Document, on=(File2Document.document_id == cls.model.id))
                .join(File, on=(File.id == File2Document.file_id))
                .where((cls.model.kb_id == kb_id), (fn.LOWER(cls.model.name).contains(keywords.lower())))
            )
        else:
            query = cls.model.select(*fields).join(File2Document, on=(File2Document.document_id == cls.model.id)).join(File, on=(File.id == File2Document.file_id)).where(cls.model.kb_id == kb_id)

        if run_status:
            query = query.where(cls.model.run.in_(run_status))
        if types:
            query = query.where(cls.model.type.in_(types))
        if suffix:
            query = query.where(cls.model.suffix.in_(suffix))

        rows = query.select(cls.model.run, cls.model.suffix, cls.model.id)
        total = rows.count()

        suffix_counter = {}
        run_status_counter = {}
        metadata_counter = {}
        empty_metadata_count = 0

        doc_ids = [row.id for row in rows]
        metadata = {}
        if doc_ids:
            try:
                metadata = DocMetadataService.get_metadata_for_documents(doc_ids, kb_id)
            except Exception as e:
                logging.warning(f"Failed to fetch metadata from ES/Infinity: {e}")

        for row in rows:
            suffix_counter[row.suffix] = suffix_counter.get(row.suffix, 0) + 1
            run_status_counter[str(row.run)] = run_status_counter.get(str(row.run), 0) + 1
            meta_fields = metadata.get(row.id, {})
            if not meta_fields:
                empty_metadata_count += 1
                continue
            has_valid_meta = False
            for key, value in meta_fields.items():
                values = value if isinstance(value, list) else [value]
                for vv in values:
                    if vv is None:
                        continue
                    if isinstance(vv, str) and not vv.strip():
                        continue
                    sv = str(vv)
                    if key not in metadata_counter:
                        metadata_counter[key] = {}
                    metadata_counter[key][sv] = metadata_counter[key].get(sv, 0) + 1
                    has_valid_meta = True
            if not has_valid_meta:
                empty_metadata_count += 1

        metadata_counter["empty_metadata"] = {"true": empty_metadata_count}
        return {
            "suffix": suffix_counter,
            "run_status": run_status_counter,
            "metadata": metadata_counter,
        }, total
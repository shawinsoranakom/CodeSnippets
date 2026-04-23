def insert(self, documents: list[dict], index_name: str, knowledgebase_id: str = None) -> list[str]:
        if not documents:
            return []

        # For doc_meta tables, use simple insert without field transformation
        if index_name.startswith("ragflow_doc_meta_"):
            return self._insert_doc_meta(documents, index_name)

        docs: list[dict] = []
        ids: list[str] = []
        for document in documents:
            d: dict = {}
            for k, v in document.items():
                if vector_column_pattern.match(k):
                    d[k] = v
                    continue
                if k not in column_names:
                    if "extra" not in d:
                        d["extra"] = {}
                    d["extra"][k] = v
                    continue
                if v is None:
                    d[k] = get_default_value(k)
                    continue

                if k == "kb_id" and isinstance(v, list):
                    d[k] = v[0]
                elif k == "content_with_weight" and isinstance(v, dict):
                    d[k] = json.dumps(v, ensure_ascii=False)
                elif k == "position_int":
                    d[k] = json.dumps([list(vv) for vv in v], ensure_ascii=False)
                elif isinstance(v, list):
                    # remove characters like '\t' for JSON dump and clean special characters
                    cleaned_v = []
                    for vv in v:
                        if isinstance(vv, str):
                            cleaned_str = vv.strip()
                            cleaned_str = cleaned_str.replace('\\', '\\\\')
                            cleaned_str = cleaned_str.replace('\n', '\\n')
                            cleaned_str = cleaned_str.replace('\r', '\\r')
                            cleaned_str = cleaned_str.replace('\t', '\\t')
                            cleaned_v.append(cleaned_str)
                        else:
                            cleaned_v.append(vv)
                    d[k] = json.dumps(cleaned_v, ensure_ascii=False)
                else:
                    d[k] = v

            ids.append(d["id"])
            # this is to fix https://github.com/sqlalchemy/sqlalchemy/issues/9703
            for column_name in column_names:
                if column_name not in d:
                    d[column_name] = get_default_value(column_name)

            metadata = d.get("metadata", {})
            if metadata is None:
                metadata = {}
            group_id = metadata.get("_group_id")
            title = metadata.get("_title")
            if d.get("doc_id"):
                if group_id:
                    d["group_id"] = group_id
                else:
                    d["group_id"] = d["doc_id"]
                if title:
                    d["docnm_kwd"] = title

            docs.append(d)

        logger.debug("OBConnection.insert chunks: %s", docs)

        res = []
        try:
            self.client.upsert(index_name, docs)
        except Exception as e:
            logger.error(f"OBConnection.insert error: {str(e)}")
            res.append(str(e))
        return res
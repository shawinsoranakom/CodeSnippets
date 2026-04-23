def get_flatted_meta_by_kbs(cls, kb_ids: List[str]) -> Dict:
        """
        Get flattened metadata for documents in knowledge bases.

        - Parses stringified JSON meta_fields when possible and skips non-dict or unparsable values.
        - Expands list values into individual entries.
          Example: {"tags": ["foo","bar"], "author": "alice"} ->
            meta["tags"]["foo"] = [doc_id], meta["tags"]["bar"] = [doc_id], meta["author"]["alice"] = [doc_id]
        Prefer for metadata_condition filtering and scenarios that must respect list semantics.

        Args:
            kb_ids: List of knowledge base IDs

        Returns:
            Metadata dictionary in format: {field_name: {value: [doc_ids]}}
        """
        try:
            # Get tenant_id from first KB
            kb = Knowledgebase.get_by_id(kb_ids[0])
            if not kb:
                return {}

            tenant_id = kb.tenant_id
            index_name = cls._get_doc_meta_index_name(tenant_id)

            condition = {"kb_id": kb_ids}
            order_by = OrderByExpr()

            # Query with large limit
            results = settings.docStoreConn.search(
                select_fields=["*"],  # Get all fields
                highlight_fields=[],
                condition=condition,
                match_expressions=[],
                order_by=order_by,
                offset=0,
                limit=10000,
                index_names=index_name,
                knowledgebase_ids=kb_ids
            )

            logging.debug(f"[get_flatted_meta_by_kbs] index_name: {index_name}, kb_ids: {kb_ids}")
            logging.debug(f"[get_flatted_meta_by_kbs] results type: {type(results)}")

            # Aggregate metadata
            meta = {}
            doc_count = 0

            # Use helper to iterate over results in any format
            for doc_id, doc in cls._iter_search_results(results):
                doc_count += 1
                # Extract metadata fields (exclude system fields)
                doc_meta = cls._extract_metadata(doc)

                for k, v in doc_meta.items():
                    if k not in meta:
                        meta[k] = {}

                    values = v if isinstance(v, list) else [v]
                    for vv in values:
                        if vv is None:
                            continue
                        sv = str(vv)
                        if sv not in meta[k]:
                            meta[k][sv] = []
                        meta[k][sv].append(doc_id)

            if doc_count >= 10000:
                logging.warning(f"[get_flatted_meta_by_kbs] Results hit the 10000 limit for KBs {kb_ids}.")

            logging.debug(f"[get_flatted_meta_by_kbs] KBs: {kb_ids}, Returning metadata: {meta}")
            return meta

        except Exception as e:
            logging.error(f"Error getting flattened metadata for KBs {kb_ids}: {e}")
            return {}
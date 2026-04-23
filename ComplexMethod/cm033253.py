def _search_metadata(cls, kb_id: str, condition: Dict = None):
        """
        Common search logic for metadata queries.
        Uses pagination internally to retrieve data from the index.

        Args:
            kb_id: Knowledge base ID
            condition: Optional search condition (defaults to {"kb_id": kb_id})

        Returns:
            Search results from ES/Infinity, or empty list if index doesn't exist
        """
        kb = Knowledgebase.get_by_id(kb_id)
        if not kb:
            return []

        tenant_id = kb.tenant_id
        index_name = cls._get_doc_meta_index_name(tenant_id)

        # Check if metadata index exists, create if it doesn't
        if not settings.docStoreConn.index_exist(index_name, ""):
            logging.debug(f"Metadata index {index_name} does not exist, creating it")
            result = settings.docStoreConn.create_doc_meta_idx(index_name)
            if result is False:
                logging.error(f"Failed to create metadata index {index_name}")
                return []
            logging.debug(f"Successfully created metadata index {index_name}")

        if condition is None:
            condition = {"kb_id": kb_id}

        # Add sort by id for ES to enable search_after on large data
        order_by = OrderByExpr()
        if not settings.DOC_ENGINE_INFINITY:
            order_by.asc("id")

        page_size = 1000
        all_results = []
        page = 0

        while True:
            results = settings.docStoreConn.search(
                select_fields=["*"],
                highlight_fields=[],
                condition=condition,
                match_expressions=[],
                order_by=order_by,
                offset=page * page_size,
                limit=page_size,
                index_names=index_name,
                knowledgebase_ids=[kb_id]
            )

            # Handle different result formats
            if results is None:
                break

            # Extract docs from results
            page_docs = []
            total_count = None  # Used for Infinity to determine if more results exist

            # Check for Infinity format first (DataFrame, total) tuple
            if isinstance(results, tuple) and len(results) == 2:
                df, total_count = results
                if hasattr(df, 'iterrows'):
                    # Pandas DataFrame from Infinity
                    page_docs = df.to_dict('records')
                else:
                    page_docs = list(df) if df else []
            # Check for ES format (dict with 'hits' key)
            elif hasattr(results, 'get') and 'hits' in results:
                hits_obj = results.get('hits', {})
                hits = hits_obj.get('hits', [])
                page_docs = []
                for hit in hits:
                    doc = hit.get('_source', {})
                    doc['id'] = hit.get('_id', '')  # Add _id as 'id' for _extract_doc_id to work
                    page_docs.append(doc)
                # Extract total count from ES response
                total_hits = hits_obj.get('total', {})
                if isinstance(total_hits, dict):
                    total_count = total_hits.get('value', len(page_docs))
                else:
                    total_count = total_hits if total_hits else len(page_docs)
            # Handle list/iterable results
            elif hasattr(results, '__iter__') and not isinstance(results, dict):
                page_docs = list(results)
            else:
                page_docs = []

            if not page_docs:
                break

            all_results.extend(page_docs)
            page += 1

            # Determine if there are more results to fetch
            # For Infinity: use total_count if available
            if total_count is not None:
                if len(all_results) >= total_count:
                    break
            else:
                # For ES or other: check if we got fewer than page_size
                if len(page_docs) < page_size:
                    break

        logging.debug(f"[_search_metadata] Retrieved {len(all_results)} total results for kb_id: {kb_id}")
        return all_results
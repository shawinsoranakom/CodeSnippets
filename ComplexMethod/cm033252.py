def _iter_search_results(cls, results):
        """
        Iterate over search results in various formats (DataFrame, ES, OceanBase, list).

        Yields:
            Tuple of (doc_id, doc_dict) for each document

        Args:
            results: Search results from ES/Infinity/OceanBase in any format
        """
        # Handle tuple return from Infinity: (DataFrame, int)
        # Check this FIRST because pandas DataFrames also have __getitem__
        if isinstance(results, tuple) and len(results) == 2:
            results = results[0]  # Extract DataFrame from tuple

        # Check if results is a pandas DataFrame (from Infinity)
        if hasattr(results, 'iterrows'):
            # Handle pandas DataFrame - use iterrows() to iterate over rows
            for _, row in results.iterrows():
                doc = dict(row)  # Convert Series to dict
                doc_id = cls._extract_doc_id(doc)
                if doc_id:
                    yield doc_id, doc

        # Check if ES format (has 'hits' key)
        # Note: ES returns ObjectApiResponse which is dict-like but not isinstance(dict)
        elif hasattr(results, 'get') and 'hits' in results:
            # ES format: {"hits": {"hits": [{"_source": {...}, "_id": "..."}]}}
            hits = results.get('hits', {}).get('hits', [])
            for hit in hits:
                doc = hit.get('_source', {})
                doc_id = cls._extract_doc_id(doc, hit)
                if doc_id:
                    yield doc_id, doc

        # Handle list of dicts or other formats
        elif isinstance(results, list):
            for res in results:
                if isinstance(res, dict):
                    docs = [res]
                else:
                    docs = res

                for doc in docs:
                    doc_id = cls._extract_doc_id(doc)
                    if doc_id:
                        yield doc_id, doc

        # Check if OceanBase SearchResult format
        elif hasattr(results, 'chunks') and hasattr(results, 'total'):
            # OceanBase format: SearchResult(total=int, chunks=[{...}, {...}])
            for doc in results.chunks:
                doc_id = cls._extract_doc_id(doc)
                if doc_id:
                    yield doc_id, doc
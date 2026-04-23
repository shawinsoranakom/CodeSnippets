def test_delete_with_chunk_ids_includes_kb_id(self):
        """
        CRITICAL: When deleting by chunk IDs, kb_id MUST be included in the query.

        This was the root cause of issue #12520 - the original code would 
        only use Q("ids") and ignore kb_id.
        """
        condition = {"id": ["chunk1", "chunk2"]}
        query = self.build_delete_query(condition, "kb123")

        query_dict = query["query"]["bool"]

        # Verify chunk IDs filter is present
        ids_filter = [f for f in query_dict.get("filter", []) if "ids" in f]
        assert len(ids_filter) == 1, "Should have ids filter"
        assert set(ids_filter[0]["ids"]["values"]) == {"chunk1", "chunk2"}

        # Verify kb_id is also in the query (CRITICAL FIX)
        must_terms = query_dict.get("must", [])
        kb_id_terms = [t for t in must_terms if "term" in t and "kb_id" in t.get("term", {})]
        assert len(kb_id_terms) == 1, "kb_id MUST be included when deleting by chunk IDs"
        assert kb_id_terms[0]["term"]["kb_id"] == "kb123"
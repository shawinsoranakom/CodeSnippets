def test_delete_with_chunk_ids_and_doc_id(self):
        """
        When deleting chunks, both chunk IDs AND doc_id should be in the query
        to properly scope the deletion to a specific document.
        """
        condition = {"id": ["chunk1"], "doc_id": "doc456"}
        query = self.build_delete_query(condition, "kb123")

        query_dict = query["query"]["bool"]

        # Verify all three conditions are present
        ids_filter = [f for f in query_dict.get("filter", []) if "ids" in f]
        assert len(ids_filter) == 1, "Should have ids filter"

        must_terms = query_dict.get("must", [])

        # Check kb_id
        kb_id_terms = [t for t in must_terms if "term" in t and "kb_id" in t.get("term", {})]
        assert len(kb_id_terms) == 1, "kb_id must be present"

        # Check doc_id
        doc_id_terms = [t for t in must_terms if "term" in t and "doc_id" in t.get("term", {})]
        assert len(doc_id_terms) == 1, "doc_id must be present"
        assert doc_id_terms[0]["term"]["doc_id"] == "doc456"
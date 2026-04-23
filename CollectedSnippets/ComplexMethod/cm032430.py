def test_delete_by_doc_id_only(self):
        """
        Delete all chunks of a document (no specific chunk IDs).
        """
        condition = {"doc_id": "doc456"}
        query = self.build_delete_query(condition, "kb123")

        query_dict = query["query"]["bool"]
        must_terms = query_dict.get("must", [])

        # Both doc_id and kb_id should be in query
        doc_terms = [t for t in must_terms if "term" in t and "doc_id" in t.get("term", {})]
        kb_terms = [t for t in must_terms if "term" in t and "kb_id" in t.get("term", {})]

        assert len(doc_terms) == 1
        assert len(kb_terms) == 1
def test_metadata_summary_counts(self, HttpApiAuth, add_documents_func):
        """
        test normal cases
        :param HttpApiAuth:
        :param add_documents_func:
        :return:
        """
        dataset_id, document_ids = add_documents_func
        payloads = [
            {"tags": ["foo", "bar"], "author": "alice"},
            {"tags": ["foo"], "author": "bob"},
            {"tags": ["bar", "baz"], "author": ""},
        ]
        for doc_id, meta_fields in zip(document_ids, payloads):
            res = update_document(HttpApiAuth, dataset_id, doc_id, {"meta_fields": meta_fields})
            assert res["code"] == 0, res

        res = metadata_summary(HttpApiAuth, dataset_id)
        assert res["code"] == 0, res

        summary = res["data"]["summary"]
        counts = _summary_to_counts(summary)
        assert counts["tags"]["foo"] == 2, counts
        assert counts["tags"]["bar"] == 2, counts
        assert counts["tags"]["baz"] == 1, counts
        assert counts["author"]["alice"] == 1, counts
        assert counts["author"]["bob"] == 1, counts
        assert "None" not in counts["author"], counts
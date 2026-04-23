def test_duplicate_deletion(self, HttpApiAuth, add_chunks_func):
        dataset_id, document_id, chunk_ids = add_chunks_func
        res = delete_chunks(HttpApiAuth, dataset_id, document_id, {"chunk_ids": chunk_ids * 2})
        assert res["code"] == 0
        assert "Duplicate chunk ids" in res["data"]["errors"][0]
        assert res["data"]["success_count"] == 4

        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]["chunks"]) == 1
        assert res["data"]["total"] == 1
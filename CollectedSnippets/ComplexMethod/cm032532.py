def test_delete_partial_invalid_id(self, HttpApiAuth, add_chunks_func, payload):
        dataset_id, document_id, chunk_ids = add_chunks_func
        if callable(payload):
            payload = payload(chunk_ids)
        res = delete_chunks(HttpApiAuth, dataset_id, document_id, payload)
        assert res["code"] == 102
        assert res["message"] == "rm_chunk deleted chunks 4, expect 5"

        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]["chunks"]) == 1
        assert res["data"]["total"] == 1
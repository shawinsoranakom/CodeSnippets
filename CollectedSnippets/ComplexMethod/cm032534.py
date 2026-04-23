def test_basic_scenarios(
        self,
        HttpApiAuth,
        add_chunks_func,
        payload,
        expected_code,
        expected_message,
        remaining,
    ):
        dataset_id, document_id, chunk_ids = add_chunks_func
        if callable(payload):
            payload = payload(chunk_ids)
        res = delete_chunks(HttpApiAuth, dataset_id, document_id, payload)
        assert res["code"] == expected_code
        if res["code"] != 0:
            assert res["message"] == expected_message

        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]["chunks"]) == remaining
        assert res["data"]["total"] == remaining
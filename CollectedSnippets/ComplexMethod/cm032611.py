def test_basic_scenarios(self, WebApiAuth, add_chunks_func, payload, expected_code, expected_message, remaining):
        _, doc_id, chunk_ids = add_chunks_func
        if callable(payload):
            payload = payload(chunk_ids)
        payload["doc_id"] = doc_id
        res = delete_chunks(WebApiAuth, payload)
        assert res["code"] == expected_code, res
        if res["code"] != 0:
            assert res["message"] == expected_message, res

        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        if res["code"] != 0:
            assert False, res
        assert len(res["data"]["chunks"]) == remaining, res
        assert res["data"]["total"] == remaining, res
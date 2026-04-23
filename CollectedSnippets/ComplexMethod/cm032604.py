def test_highlight(self, WebApiAuth, add_chunks, payload, expected_code, expected_highlight, expected_message):
        dataset_id, _, _ = add_chunks
        payload.update({"question": "chunk", "kb_id": [dataset_id]})
        res = retrieval_chunks(WebApiAuth, payload)
        assert res["code"] == expected_code, res
        if expected_highlight:
            for chunk in res["data"]["chunks"]:
                assert "highlight" in chunk, res
        else:
            for chunk in res["data"]["chunks"]:
                assert "highlight" not in chunk, res

        if expected_code != 0:
            assert res["message"] == expected_message, res
def test_highlight(self, HttpApiAuth, add_chunks, payload, expected_code, expected_highlight, expected_message):
        dataset_id, _, _ = add_chunks
        payload.update({"question": "chunk", "dataset_ids": [dataset_id]})
        res = retrieval_chunks(HttpApiAuth, payload)
        assert res["code"] == expected_code
        if expected_highlight:
            for chunk in res["data"]["chunks"]:
                assert "highlight" in chunk
        else:
            for chunk in res["data"]["chunks"]:
                assert "highlight" not in chunk

        if expected_code != 0:
            assert res["message"] == expected_message
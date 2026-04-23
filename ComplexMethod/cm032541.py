def test_id(
        self,
        HttpApiAuth,
        add_chunks,
        chunk_id,
        expected_code,
        expected_page_size,
        expected_message,
    ):
        dataset_id, document_id, chunk_ids = add_chunks
        if callable(chunk_id):
            params = {"id": chunk_id(chunk_ids)}
        else:
            params = {"id": chunk_id}
        res = list_chunks(HttpApiAuth, dataset_id, document_id, params=params)
        assert res["code"] == expected_code
        if expected_code == 0:
            if params["id"] in [None, ""]:
                assert len(res["data"]["chunks"]) == expected_page_size
            else:
                assert res["data"]["chunks"][0]["id"] == params["id"]
        else:
            assert res["message"] == expected_message
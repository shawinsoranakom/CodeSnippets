def test_id(
            self,
            HttpApiAuth,
            add_documents,
            document_id,
            expected_code,
            expected_num,
            expected_message,
    ):
        dataset_id, document_ids = add_documents
        if callable(document_id):
            params = {"id": document_id(document_ids)}
        else:
            params = {"id": document_id}
        res = list_documents(HttpApiAuth, dataset_id, params=params)

        assert res["code"] == expected_code
        if expected_code == 0:
            if params["id"] in [None, ""]:
                assert len(res["data"]["docs"]) == expected_num
            else:
                doc = res["data"]["docs"][0]
                assert doc["id"] == params["id"]
        else:
            assert res["message"] == expected_message
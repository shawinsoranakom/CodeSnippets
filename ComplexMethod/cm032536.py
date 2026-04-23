def test_content(self, HttpApiAuth, add_document, payload, expected_code, expected_message):
        dataset_id, document_id = add_document
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        chunks_count = res["data"]["doc"]["chunk_count"]
        res = add_chunk(HttpApiAuth, dataset_id, document_id, payload)
        assert res["code"] == expected_code, res
        if expected_code == 0:
            validate_chunk_details(dataset_id, document_id, payload, res)
            res = list_chunks(HttpApiAuth, dataset_id, document_id)
            if res["code"] != 0:
                assert False, res
            assert res["data"]["doc"]["chunk_count"] == chunks_count + 1
        else:
            assert res["message"] == expected_message
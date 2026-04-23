def test_repeated_add_chunk(self, HttpApiAuth, add_document):
        payload = {"content": "chunk test"}
        dataset_id, document_id = add_document
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        chunks_count = res["data"]["doc"]["chunk_count"]
        res = add_chunk(HttpApiAuth, dataset_id, document_id, payload)
        assert res["code"] == 0
        validate_chunk_details(dataset_id, document_id, payload, res)
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert res["data"]["doc"]["chunk_count"] == chunks_count + 1

        res = add_chunk(HttpApiAuth, dataset_id, document_id, payload)
        assert res["code"] == 0
        validate_chunk_details(dataset_id, document_id, payload, res)
        res = list_chunks(HttpApiAuth, dataset_id, document_id)
        if res["code"] != 0:
            assert False, res
        assert res["data"]["doc"]["chunk_count"] == chunks_count + 2
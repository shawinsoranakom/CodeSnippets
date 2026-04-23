def test_repeated_add_chunk(self, WebApiAuth, add_document):
        payload = {"content_with_weight": "chunk test"}
        kb_id, doc_id = add_document
        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        if res["code"] != 0:
            assert False, res
        chunks_count = res["data"]["doc"]["chunk_num"]

        res = add_chunk(WebApiAuth, {**payload, "doc_id": doc_id})
        assert res["code"] == 0, res
        validate_chunk_details(WebApiAuth, kb_id, doc_id, payload, res)
        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        if res["code"] != 0:
            assert False, res
        assert res["data"]["doc"]["chunk_num"] == chunks_count + 1, res

        res = add_chunk(WebApiAuth, {**payload, "doc_id": doc_id})
        assert res["code"] == 0, res
        validate_chunk_details(WebApiAuth, kb_id, doc_id, payload, res)
        res = list_chunks(WebApiAuth, {"doc_id": doc_id})
        if res["code"] != 0:
            assert False, res
        assert res["data"]["doc"]["chunk_num"] == chunks_count + 2, res
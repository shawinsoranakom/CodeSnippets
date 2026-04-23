def test_important_keywords(self, WebApiAuth, add_chunks, payload, expected_code, expected_message):
        _, doc_id, chunk_ids = add_chunks
        chunk_id = chunk_ids[0]
        update_payload = {"doc_id": doc_id, "chunk_id": chunk_id, "content_with_weight": "unchanged content"}  # Add content_with_weight as it's required
        if payload:
            update_payload.update(payload)
        res = update_chunk(WebApiAuth, update_payload)
        assert res["code"] == expected_code, res
        if expected_code != 0:
            assert res["message"] == expected_message, res
        else:
            sleep(1)
            res = list_chunks(WebApiAuth, {"doc_id": doc_id})
            for chunk in res["data"]["chunks"]:
                if chunk["chunk_id"] == chunk_id:
                    assert chunk["important_kwd"] == payload["important_kwd"]
def validate_chunk_details(auth, kb_id, doc_id, payload, res):
    chunk_id = res["data"]["chunk_id"]
    res = get_chunk(auth, {"chunk_id": chunk_id})
    assert res["code"] == 0, res
    chunk = res["data"]
    assert chunk["doc_id"] == doc_id
    assert chunk["kb_id"] == kb_id
    assert chunk["content_with_weight"] == payload["content_with_weight"]
    if "important_kwd" in payload:
        assert chunk["important_kwd"] == payload["important_kwd"]
    if "question_kwd" in payload:
        expected = [str(q).strip() for q in payload.get("question_kwd", [])]
        assert chunk["question_kwd"] == expected
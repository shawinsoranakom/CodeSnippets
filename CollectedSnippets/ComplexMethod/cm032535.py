def validate_chunk_details(dataset_id, document_id, payload, res):
    chunk = res["data"]["chunk"]
    assert chunk["dataset_id"] == dataset_id
    assert chunk["document_id"] == document_id
    assert chunk["content"] == payload["content"]
    if "important_keywords" in payload:
        assert chunk["important_keywords"] == payload["important_keywords"]
    if "questions" in payload:
        assert chunk["questions"] == [str(q).strip() for q in payload.get("questions", []) if str(q).strip()]
    if "tag_kwd" in payload:
        assert chunk["tag_kwd"] == payload["tag_kwd"]
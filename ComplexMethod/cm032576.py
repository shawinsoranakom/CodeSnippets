def validate_document_parse_done(auth, _kb_id, _document_ids):
    res = list_documents(auth, {"kb_id": _kb_id})
    for doc in res["data"]["docs"]:
        if doc["id"] not in _document_ids:
            continue
        assert doc["run"] == "DONE"
        assert len(doc["process_begin_at"]) > 0
        assert doc["process_duration"] > 0
        assert doc["progress"] > 0
        assert "Task done" in doc["progress_msg"]
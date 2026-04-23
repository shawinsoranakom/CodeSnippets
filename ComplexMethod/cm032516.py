def test_build_reference_chunks_metadata_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)

    monkeypatch.setattr(module, "chunks_format", lambda _reference: [{"dataset_id": "kb-1", "document_id": "doc-1"}])
    res = module._build_reference_chunks([], include_metadata=False)
    assert res == [{"dataset_id": "kb-1", "document_id": "doc-1"}]

    monkeypatch.setattr(module, "chunks_format", lambda _reference: [{"dataset_id": "kb-1"}, {"document_id": "doc-2"}])
    res = module._build_reference_chunks([], include_metadata=True)
    assert all("document_metadata" not in chunk for chunk in res)

    monkeypatch.setattr(module, "chunks_format", lambda _reference: [{"dataset_id": "kb-1", "document_id": "doc-1"}])
    monkeypatch.setattr(module.DocMetadataService, "get_metadata_for_documents", lambda _doc_ids, _kb_id: {"doc-1": {"author": "alice"}})
    res = module._build_reference_chunks([], include_metadata=True, metadata_fields=[1, None])
    assert "document_metadata" not in res[0]

    source_chunks = [
        {"dataset_id": "kb-1", "document_id": "doc-1"},
        {"dataset_id": "kb-2", "document_id": "doc-2"},
        {"dataset_id": "kb-1", "document_id": "doc-3"},
        {"dataset_id": "kb-1", "document_id": None},
    ]
    monkeypatch.setattr(module, "chunks_format", lambda _reference: [dict(chunk) for chunk in source_chunks])

    def _get_metadata(_doc_ids, kb_id):
        if kb_id == "kb-1":
            return {"doc-1": {"author": "alice", "year": 2024}}
        if kb_id == "kb-2":
            return {"doc-2": {"author": "bob", "tag": "rag"}}
        return {}

    monkeypatch.setattr(module.DocMetadataService, "get_metadata_for_documents", _get_metadata)
    res = module._build_reference_chunks([], include_metadata=True, metadata_fields=["author", "missing", 3])
    assert res[0]["document_metadata"] == {"author": "alice"}
    assert res[1]["document_metadata"] == {"author": "bob"}
    assert "document_metadata" not in res[2]
    assert "document_metadata" not in res[3]
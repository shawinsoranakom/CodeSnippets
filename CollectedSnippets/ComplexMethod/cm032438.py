def test_async_ask_delta_events_carry_incremental_text_only(monkeypatch):
    """
    Intermediate delta events must have empty reference dicts.
    Only the final event should carry the populated reference from decorate_answer().
    """
    chat_mdl = _StreamingChatModel("Incremental text for delta test.")
    retriever = _StubRetriever()

    monkeypatch.setattr(
        dialog_service.KnowledgebaseService, "get_by_ids", lambda _ids: [_KB]
    )
    monkeypatch.setattr(
        dialog_service, "get_model_config_by_type_and_name",
        lambda _tid, _type, _name: _LLM_CONFIG,
    )
    monkeypatch.setattr(dialog_service, "LLMBundle", lambda _tid, _cfg: chat_mdl)
    monkeypatch.setattr(dialog_service.settings, "retriever", retriever, raising=False)
    monkeypatch.setattr(dialog_service.settings, "kg_retriever", retriever, raising=False)
    monkeypatch.setattr(
        dialog_service.DocMetadataService, "get_flatted_meta_by_kbs", lambda _ids: {}
    )
    monkeypatch.setattr(dialog_service, "label_question", lambda _q, _kbs: "")
    monkeypatch.setattr(
        dialog_service, "kb_prompt",
        lambda _kbinfos, _max_tokens, **_kw: ["RAGFlow is a RAG engine."],
    )

    events = _collect(
        dialog_service.async_ask(
            question="Describe RAGFlow briefly.",
            kb_ids=["kb-1"],
            tenant_id="tenant-1",
        )
    )

    delta_events = [e for e in events if not e.get("final")]
    final_events  = [e for e in events if e.get("final") is True]

    assert len(final_events) == 1, f"Expected exactly one final event, got {len(final_events)}"
    for ev in delta_events:
        assert ev["reference"] == {}, f"Delta event must have empty reference, got: {ev['reference']}"

    assert "chunks" in final_events[0]["reference"], (
        "Final event reference must contain chunk data from decorate_answer()"
    )
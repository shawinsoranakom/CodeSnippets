def test_tts_embedded_stream_and_error_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.tts)
    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"text": "A。B"}))
    monkeypatch.setattr(module, "Response", _StubResponse)

    tenant_llm_service = sys.modules["api.db.services.tenant_llm_service"]
    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (False, None))
    res = _run(handler("tenant-1"))
    assert res["message"] == "Tenant not found!"

    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (True, SimpleNamespace(asr_id="", tts_id="", llm_id="", embd_id="", img2txt_id="", rerank_id="")))
    res = _run(handler("tenant-1"))
    assert res["message"] == "No default TTS model is set"

    class _TTSOk:
        def tts(self, txt):
            if not txt:
                return []
            yield f"chunk-{txt}".encode("utf-8")

    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (True, SimpleNamespace(asr_id="", tts_id="tts-x", llm_id="", embd_id="", img2txt_id="", rerank_id="")))
    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: _TTSOk())
    resp = _run(handler("tenant-1"))
    assert resp.mimetype == "audio/mpeg"
    assert resp.headers.get("Cache-Control") == "no-cache"
    assert resp.headers.get("Connection") == "keep-alive"
    assert resp.headers.get("X-Accel-Buffering") == "no"
    chunks = _run(_collect_stream(resp.body))
    assert any("chunk-A" in chunk for chunk in chunks)
    assert any("chunk-B" in chunk for chunk in chunks)

    class _TTSErr:
        def tts(self, _txt):
            raise RuntimeError("tts boom")

    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: _TTSErr())
    resp = _run(handler("tenant-1"))
    chunks = _run(_collect_stream(resp.body))
    assert any('"code": 500' in chunk and "**ERROR**: tts boom" in chunk for chunk in chunks)
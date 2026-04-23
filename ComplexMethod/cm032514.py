def test_sequence2txt_embedded_validation_and_stream_matrix_unit(monkeypatch):
    module = _load_session_module(monkeypatch)
    handler = inspect.unwrap(module.sequence2txt)
    monkeypatch.setattr(module, "Response", _StubResponse)
    monkeypatch.setattr(module.tempfile, "mkstemp", lambda suffix: (11, f"/tmp/audio{suffix}"))
    monkeypatch.setattr(module.os, "close", lambda _fd: None)

    def _set_request(form, files):
        monkeypatch.setattr(
            module,
            "request",
            SimpleNamespace(form=_AwaitableValue(form), files=_AwaitableValue(files)),
        )

    _set_request({"stream": "false"}, {})
    res = _run(handler("tenant-1"))
    assert "Missing 'file' in multipart form-data" in res["message"]

    _set_request({"stream": "false"}, {"file": _DummyUploadFile("bad.txt")})
    res = _run(handler("tenant-1"))
    assert "Unsupported audio format: .txt" in res["message"]

    _set_request({"stream": "false"}, {"file": _DummyUploadFile("audio.wav")})
    tenant_llm_service = sys.modules["api.db.services.tenant_llm_service"]
    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (False, None))
    res = _run(handler("tenant-1"))
    assert res["message"] == "Tenant not found!"

    _set_request({"stream": "false"}, {"file": _DummyUploadFile("audio.wav")})
    tenant_llm_service = sys.modules["api.db.services.tenant_llm_service"]
    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (True, SimpleNamespace(asr_id="", tts_id="", llm_id="", embd_id="", img2txt_id="", rerank_id="")))
    res = _run(handler("tenant-1"))
    assert res["message"] == "No default ASR model is set"

    class _SyncASR:
        def transcription(self, _path):
            return "transcribed text"

        def stream_transcription(self, _path):
            return []

    _set_request({"stream": "false"}, {"file": _DummyUploadFile("audio.wav")})
    monkeypatch.setattr(tenant_llm_service.TenantService, "get_by_id", lambda _tid: (True, SimpleNamespace(asr_id="asr-x", tts_id="", llm_id="", embd_id="", img2txt_id="", rerank_id="")))
    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: _SyncASR())
    monkeypatch.setattr(module.os, "remove", lambda _path: (_ for _ in ()).throw(RuntimeError("cleanup fail")))
    res = _run(handler("tenant-1"))
    assert res["code"] == 0
    assert res["data"]["text"] == "transcribed text"

    class _StreamASR:
        def transcription(self, _path):
            return ""

        def stream_transcription(self, _path):
            yield {"event": "partial", "text": "hello"}

    _set_request({"stream": "true"}, {"file": _DummyUploadFile("audio.wav")})
    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: _StreamASR())
    monkeypatch.setattr(module.os, "remove", lambda _path: None)
    resp = _run(handler("tenant-1"))
    assert isinstance(resp, _StubResponse)
    assert resp.content_type == "text/event-stream"
    chunks = _run(_collect_stream(resp.body))
    assert any('"event": "partial"' in chunk for chunk in chunks)

    class _ErrorASR:
        def transcription(self, _path):
            return ""

        def stream_transcription(self, _path):
            raise RuntimeError("stream asr boom")

    _set_request({"stream": "true"}, {"file": _DummyUploadFile("audio.wav")})
    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: _ErrorASR())
    monkeypatch.setattr(module.os, "remove", lambda _path: (_ for _ in ()).throw(RuntimeError("cleanup boom")))
    resp = _run(handler("tenant-1"))
    chunks = _run(_collect_stream(resp.body))
    assert any("stream asr boom" in chunk for chunk in chunks)
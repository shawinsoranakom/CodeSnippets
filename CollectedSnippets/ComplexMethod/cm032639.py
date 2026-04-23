def test_add_llm_model_type_probe_and_persistence_matrix_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)

    async def _wait_for(coro, *_args, **_kwargs):
        return await coro

    async def _to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(module.asyncio, "wait_for", _wait_for)
    monkeypatch.setattr(module.asyncio, "to_thread", _to_thread)
    monkeypatch.setattr(
        module,
        "get_allowed_llm_factories",
        lambda: [
            SimpleNamespace(name=name)
            for name in [
                "FEmbFail",
                "FEmbPass",
                "FChatFail",
                "FChatPass",
                "FRKey",
                "FRFail",
                "FImgFail",
                "FTTSFail",
                "FOcrFail",
                "FSttFail",
                "FUnknown",
            ]
        ],
    )

    class _EmbeddingFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, _texts):
            return [[]], 1

    class _EmbeddingPass:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, _texts):
            return [[0.5]], 1

    class _ChatFail:
        def __init__(self, *_args, **_kwargs):
            pass

        async def async_chat(self, *_args, **_kwargs):
            return "**ERROR**: chat failed", 0

        async def async_chat_streamly(self, *_args, **_kwargs):
            yield "**ERROR**: chat failed"
            yield 0

    class _ChatPass:
        def __init__(self, *_args, **_kwargs):
            pass

        async def async_chat(self, *_args, **_kwargs):
            return "ok", 1

        async def async_chat_streamly(self, *_args, **_kwargs):
            yield "ok"
            yield 1

    class _RerankFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def similarity(self, *_args, **_kwargs):
            return [], 1

    class _CvFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def describe(self, _image_data):
            return "**ERROR**: image failed", 0

    class _TTSFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def tts(self, _text):
            raise RuntimeError("tts fail")
            yield b"x"

    class _OcrFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def check_available(self):
            return False, "ocr unavailable"

    class _SttFail:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("stt fail")

    class _RerankKeyMap(dict):
        def __contains__(self, key):
            if key == "FRKey":
                return True
            return super().__contains__(key)

        def __getitem__(self, key):
            if key == "FRKey":
                raise KeyError("rerank key fail")
            return super().__getitem__(key)

    monkeypatch.setattr(module, "EmbeddingModel", {"FEmbFail": _EmbeddingFail, "FEmbPass": _EmbeddingPass})
    monkeypatch.setattr(module, "ChatModel", {"FChatFail": _ChatFail, "FChatPass": _ChatPass})
    monkeypatch.setattr(module, "RerankModel", _RerankKeyMap({"FRFail": _RerankFail}))
    monkeypatch.setattr(module, "CvModel", {"FImgFail": _CvFail})
    monkeypatch.setattr(module, "TTSModel", {"FTTSFail": _TTSFail})
    monkeypatch.setattr(module, "OcrModel", {"FOcrFail": _OcrFail})
    monkeypatch.setattr(module, "Seq2txtModel", {"FSttFail": _SttFail})

    def _call(req):
        _set_request_json(monkeypatch, module, req)
        return _run(module.add_llm())

    res = _call({"llm_factory": "FEmbFail", "llm_name": "m", "model_type": module.LLMType.EMBEDDING.value, "verify": True})
    assert res["code"] == 0
    assert res["data"]["success"] is False
    assert "Fail to access embedding model(m)." in res["data"]["message"]

    res = _call({"llm_factory": "FEmbFail", "llm_name": "m", "model_type": module.LLMType.EMBEDDING.value})
    assert res["code"] == 400
    assert "Fail to access embedding model(m)." in res["message"]

    res = _call({"llm_factory": "FChatFail", "llm_name": "m", "model_type": module.LLMType.CHAT.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FChatFail/m)." in res["data"]["message"]

    res = _call({"llm_factory": "FRKey", "llm_name": "m", "model_type": module.LLMType.RERANK.value, "verify": True})
    assert res["code"] == 0
    assert "dose not support this model(FRKey/m)" in res["data"]["message"]

    res = _call({"llm_factory": "FRFail", "llm_name": "m", "model_type": module.LLMType.RERANK.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FRFail/m)." in res["data"]["message"]

    res = _call({"llm_factory": "FImgFail", "llm_name": "m", "model_type": module.LLMType.IMAGE2TEXT.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FImgFail/m)." in res["data"]["message"]

    res = _call({"llm_factory": "FTTSFail", "llm_name": "m", "model_type": module.LLMType.TTS.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FTTSFail/m)." in res["data"]["message"]

    res = _call({"llm_factory": "FOcrFail", "llm_name": "m", "model_type": module.LLMType.OCR.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FOcrFail/m)." in res["data"]["message"]

    res = _call({"llm_factory": "FSttFail", "llm_name": "m", "model_type": module.LLMType.SPEECH2TEXT.value, "verify": True})
    assert res["code"] == 0
    assert "Fail to access model(FSttFail/m)." in res["data"]["message"]

    _set_request_json(monkeypatch, module, {"llm_factory": "FUnknown", "llm_name": "m", "model_type": "unknown"})
    with pytest.raises(RuntimeError, match="Unknown model type: unknown"):
        _run(module.add_llm())

    saved = []
    monkeypatch.setattr(module.TenantLLMService, "filter_update", lambda _filters, _payload: False)
    monkeypatch.setattr(module.TenantLLMService, "save", lambda **kwargs: saved.append(kwargs) or True)
    res = _call({"llm_factory": "FChatPass", "llm_name": "m", "model_type": module.LLMType.CHAT.value, "api_key": "k"})
    assert res["code"] == 0, res["message"]
    assert res["data"] is True
    assert saved
    assert saved[0]["llm_factory"] == "FChatPass"
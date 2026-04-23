def test_set_api_key_model_probe_matrix_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)

    async def _wait_for(coro, *_args, **_kwargs):
        return await coro

    async def _to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(module.asyncio, "wait_for", _wait_for)
    monkeypatch.setattr(module.asyncio, "to_thread", _to_thread)

    class _EmbeddingFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, _texts):
            return [[]], 1

    class _EmbeddingPass:
        def __init__(self, *_args, **_kwargs):
            pass

        def encode(self, _texts):
            return [[0.1]], 1

    class _ChatFail:
        def __init__(self, *_args, **_kwargs):
            pass

        async def async_chat(self, *_args, **_kwargs):
            return "**ERROR** chat fail", 1

    class _RerankFail:
        def __init__(self, *_args, **_kwargs):
            pass

        def similarity(self, *_args, **_kwargs):
            return [], 0

    factory = "FactoryA"
    monkeypatch.setattr(
        module.LLMService,
        "query",
        lambda **_kwargs: [
            _LLMRow(llm_name="emb", fid=factory, model_type=module.LLMType.EMBEDDING.value, max_tokens=321),
            _LLMRow(llm_name="chat", fid=factory, model_type=module.LLMType.CHAT.value, max_tokens=654),
            _LLMRow(llm_name="rerank", fid=factory, model_type=module.LLMType.RERANK.value, max_tokens=987),
        ],
    )
    monkeypatch.setattr(module, "EmbeddingModel", {factory: _EmbeddingFail})
    monkeypatch.setattr(module, "ChatModel", {factory: _ChatFail})
    monkeypatch.setattr(module, "RerankModel", {factory: _RerankFail})

    req = {"llm_factory": factory, "api_key": "k", "base_url": "http://x", "verify": True}
    _set_request_json(monkeypatch, module, req)
    res = _run(module.set_api_key())
    assert res["code"] == 0
    assert res["data"]["success"] is False
    assert "Fail to access embedding model(emb)" in res["data"]["message"]
    assert "Fail to access model(FactoryA/chat)" in res["data"]["message"]
    assert "Fail to access model(FactoryA/rerank)" in res["data"]["message"]

    req["verify"] = False
    _set_request_json(monkeypatch, module, req)
    res = _run(module.set_api_key())
    assert res["code"] == 400
    assert "Fail to access embedding model(emb)" in res["message"]

    calls = {"filter_update": [], "save": []}

    def _filter_update(filters, payload):
        calls["filter_update"].append((filters, dict(payload)))
        return False

    def _save(**kwargs):
        calls["save"].append(kwargs)
        return True

    monkeypatch.setattr(module, "EmbeddingModel", {factory: _EmbeddingPass})
    monkeypatch.setattr(module.LLMService, "query", lambda **_kwargs: [_LLMRow(llm_name="emb-pass", fid=factory, model_type=module.LLMType.EMBEDDING.value, max_tokens=2049)])
    monkeypatch.setattr(module.TenantLLMService, "filter_update", _filter_update)
    monkeypatch.setattr(module.TenantLLMService, "save", _save)

    success_req = {
        "llm_factory": factory,
        "api_key": "k2",
        "base_url": "http://y",
        "model_type": "chat",
        "llm_name": "manual-model",
    }
    _set_request_json(monkeypatch, module, success_req)
    res = _run(module.set_api_key())
    assert res["code"] == 0
    assert res["data"] is True
    assert calls["filter_update"]
    assert calls["filter_update"][0][1]["model_type"] == "chat"
    assert calls["filter_update"][0][1]["llm_name"] == "manual-model"
    assert calls["filter_update"][0][1]["max_tokens"] == 2049
    assert calls["save"][0]["max_tokens"] == 2049
    assert calls["save"][0]["llm_name"] == "emb-pass"
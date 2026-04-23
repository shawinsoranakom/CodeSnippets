def test_add_llm_factory_specific_key_assembly_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)

    async def _wait_for(coro, *_args, **_kwargs):
        return await coro

    async def _to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    monkeypatch.setattr(module.asyncio, "wait_for", _wait_for)
    monkeypatch.setattr(module.asyncio, "to_thread", _to_thread)

    allowed = [
        "VolcEngine",
        "Tencent Cloud",
        "Bedrock",
        "LocalAI",
        "HuggingFace",
        "OpenAI-API-Compatible",
        "VLLM",
        "XunFei Spark",
        "BaiduYiyan",
        "Fish Audio",
        "Google Cloud",
        "Azure-OpenAI",
        "OpenRouter",
        "MinerU",
        "PaddleOCR",
    ]
    monkeypatch.setattr(module, "get_allowed_llm_factories", lambda: [SimpleNamespace(name=name) for name in allowed])

    captured = {"chat": [], "tts": [], "filter_payloads": []}

    class _ChatOK:
        def __init__(self, key, model_name, base_url="", **_kwargs):
            captured["chat"].append((key, model_name, base_url))

        async def async_chat(self, *_args, **_kwargs):
            return "ok", 1

        async def async_chat_streamly(self, *_args, **_kwargs):
            yield "ok"
            yield 1

    class _TTSOK:
        def __init__(self, key, model_name, base_url="", **_kwargs):
            captured["tts"].append((key, model_name, base_url))

        def tts(self, _text):
            yield b"ok"

    monkeypatch.setattr(module, "ChatModel", {name: _ChatOK for name in allowed})
    monkeypatch.setattr(module, "TTSModel", {"XunFei Spark": _TTSOK})
    monkeypatch.setattr(module.TenantLLMService, "filter_update", lambda _filters, payload: captured["filter_payloads"].append(dict(payload)) or True)

    reject_req = {"llm_factory": "NotAllowed", "llm_name": "x", "model_type": module.LLMType.CHAT.value}
    _set_request_json(monkeypatch, module, reject_req)
    res = _run(module.add_llm())
    assert res["code"] == 400
    assert "is not allowed" in res["message"]

    def _run_case(factory, *, model_type=module.LLMType.CHAT.value, extra=None):
        req = {"llm_factory": factory, "llm_name": "model", "model_type": model_type, "api_key": "k", "api_base": "http://api"}
        if extra:
            req.update(extra)
        _set_request_json(monkeypatch, module, req)
        out = _run(module.add_llm())
        assert out["code"] == 0
        assert out["data"] is True
        return captured["filter_payloads"][-1]

    volc = _run_case("VolcEngine", extra={"ark_api_key": "ak", "endpoint_id": "eid"})
    assert json.loads(volc["api_key"]) == {"ark_api_key": "ak", "endpoint_id": "eid"}

    bedrock = _run_case(
        "Bedrock",
        extra={"auth_mode": "iam", "bedrock_ak": "ak", "bedrock_sk": "sk", "bedrock_region": "r", "aws_role_arn": "arn"},
    )
    assert json.loads(bedrock["api_key"]) == {
        "auth_mode": "iam",
        "bedrock_ak": "ak",
        "bedrock_sk": "sk",
        "bedrock_region": "r",
        "aws_role_arn": "arn",
    }

    localai = _run_case("LocalAI")
    assert localai["llm_name"] == "model___LocalAI"
    huggingface = _run_case("HuggingFace")
    assert huggingface["llm_name"] == "model___HuggingFace"
    openapi = _run_case("OpenAI-API-Compatible")
    assert openapi["llm_name"] == "model___OpenAI-API"
    vllm = _run_case("VLLM")
    assert vllm["llm_name"] == "model___VLLM"

    spark_chat = _run_case("XunFei Spark", extra={"spark_api_password": "spark-pass"})
    assert spark_chat["api_key"] == "spark-pass"
    spark_tts = _run_case(
        "XunFei Spark",
        model_type=module.LLMType.TTS.value,
        extra={"spark_app_id": "app", "spark_api_secret": "secret", "spark_api_key": "key"},
    )
    assert json.loads(spark_tts["api_key"]) == {
        "spark_app_id": "app",
        "spark_api_secret": "secret",
        "spark_api_key": "key",
    }

    baidu = _run_case("BaiduYiyan", extra={"yiyan_ak": "ak", "yiyan_sk": "sk"})
    assert json.loads(baidu["api_key"]) == {"yiyan_ak": "ak", "yiyan_sk": "sk"}
    fish = _run_case("Fish Audio", extra={"fish_audio_ak": "ak", "fish_audio_refid": "rid"})
    assert json.loads(fish["api_key"]) == {"fish_audio_ak": "ak", "fish_audio_refid": "rid"}
    google = _run_case(
        "Google Cloud",
        extra={"google_project_id": "pid", "google_region": "us", "google_service_account_key": "sak"},
    )
    assert json.loads(google["api_key"]) == {
        "google_project_id": "pid",
        "google_region": "us",
        "google_service_account_key": "sak",
    }
    azure = _run_case("Azure-OpenAI", extra={"api_key": "real-key", "api_version": "2024-01-01"})
    assert json.loads(azure["api_key"]) == {"api_key": "real-key", "api_version": "2024-01-01"}
    openrouter = _run_case("OpenRouter", extra={"api_key": "or-key", "provider_order": "a,b"})
    assert json.loads(openrouter["api_key"]) == {"api_key": "or-key", "provider_order": "a,b"}
    mineru = _run_case("MinerU", extra={"api_key": "m-key", "provider_order": "p1"})
    assert json.loads(mineru["api_key"]) == {"api_key": "m-key", "provider_order": "p1"}
    paddle = _run_case("PaddleOCR", extra={"api_key": "p-key", "provider_order": "p2"})
    assert json.loads(paddle["api_key"]) == {"api_key": "p-key", "provider_order": "p2"}

    tencent_req = {
        "llm_factory": "Tencent Cloud",
        "llm_name": "model",
        "model_type": module.LLMType.CHAT.value,
        "tencent_cloud_sid": "sid",
        "tencent_cloud_sk": "sk",
    }

    async def _tencent_request_json():
        return tencent_req

    monkeypatch.setattr(module, "get_request_json", _tencent_request_json)
    delegated = {}

    async def _fake_set_api_key():
        delegated["api_key"] = tencent_req.get("api_key")
        return {"code": 0, "data": "delegated"}

    monkeypatch.setattr(module, "set_api_key", _fake_set_api_key)
    res = _run(module.add_llm())
    assert res["code"] == 0
    assert res["data"] == "delegated"
    assert json.loads(delegated["api_key"]) == {"tencent_cloud_sid": "sid", "tencent_cloud_sk": "sk"}
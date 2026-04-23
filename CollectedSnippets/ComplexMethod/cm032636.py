def test_factories_route_success_and_exception_unit(monkeypatch):
    module = _load_llm_app(monkeypatch)

    def _factory(name):
        return SimpleNamespace(name=name, to_dict=lambda n=name: {"name": n})

    monkeypatch.setattr(
        module,
        "get_allowed_llm_factories",
        lambda: [
            _factory("OpenAI"),
            _factory("CustomFactory"),
            _factory("FastEmbed"),
            _factory("Builtin"),
        ],
    )
    monkeypatch.setattr(
        module.LLMService,
        "get_all",
        lambda: [
            _LLMRow(llm_name="m1", fid="OpenAI", model_type="chat", status="1"),
            _LLMRow(llm_name="m2", fid="OpenAI", model_type="embedding", status="1"),
            _LLMRow(llm_name="m3", fid="OpenAI", model_type="rerank", status="0"),
        ],
    )
    res = module.factories()
    assert res["code"] == 0
    names = [item["name"] for item in res["data"]]
    assert "FastEmbed" not in names
    assert "Builtin" not in names
    assert {"OpenAI", "CustomFactory"} == set(names)
    openai = next(item for item in res["data"] if item["name"] == "OpenAI")
    assert {"chat", "embedding"} == set(openai["model_types"])

    monkeypatch.setattr(module, "get_allowed_llm_factories", lambda: (_ for _ in ()).throw(RuntimeError("factories boom")))
    res = module.factories()
    assert res["code"] == 500
    assert "factories boom" in res["message"]
def test_check_embedding_similarity_threshold_matrix_unit(monkeypatch):
    module = _load_kb_module(monkeypatch)
    route = inspect.unwrap(module.check_embedding)
    monkeypatch.setattr(
        module,
        "get_model_config_by_type_and_name",
        lambda *_args, **_kwargs: {"llm_factory": "test", "llm_name": "emb-1", "model_type": module.LLMType.EMBEDDING.value},
    )
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, SimpleNamespace(tenant_id="tenant-1")))
    monkeypatch.setattr(module.search, "index_name", lambda _tenant_id: "idx")

    class _FlipBool:
        def __init__(self):
            self._calls = 0

        def __bool__(self):
            self._calls += 1
            return self._calls == 1

    monkeypatch.setattr(
        module.re,
        "sub",
        lambda _pattern, _repl, text: _FlipBool() if "TRIGGER_NO_TEXT" in str(text) else text,
    )

    def _fixed_sample(population, k):
        return list(population)[:k]

    monkeypatch.setattr(module.random, "sample", _fixed_sample)

    class _DocStore:
        def __init__(self, total, ids_by_offset, docs):
            self.total = total
            self.ids_by_offset = ids_by_offset
            self.docs = docs

        def search(self, select_fields, **kwargs):
            if not select_fields:
                return {"kind": "total"}
            return {"kind": "sample", "offset": kwargs["offset"]}

        def get_total(self, _res):
            return self.total

        def get_doc_ids(self, res):
            return self.ids_by_offset.get(res.get("offset", -1), [])

        def get(self, cid, _index_name, _kb_ids):
            return self.docs.get(cid, {})

    class _EmbModel:
        def __init__(self):
            self.calls = []

        def encode(self, pair):
            title, _txt = pair
            self.calls.append(title)
            if title == "Doc Mix":
                # title+content mix wins over content only path.
                return [module.np.array([1.0, 0.0]), module.np.array([0.0, 1.0])], None
            if title == "Doc High":
                return [module.np.array([1.0, 0.0]), module.np.array([1.0, 0.0])], None
            return [module.np.array([0.0, 1.0]), module.np.array([0.0, 1.0])], None

    emb_model = _EmbModel()
    monkeypatch.setattr(module, "LLMBundle", lambda *_args, **_kwargs: emb_model)

    low_docs = {
        "chunk-no-vec": {
            "doc_id": "doc-no-vec",
            "docnm_kwd": "Doc No Vec",
            "content_with_weight": "body-no-vec",
            "page_num_int": 1,
            "position_int": 1,
            "top_int": 1,
        },
        "chunk-bad-type": {
            "doc_id": "doc-bad-type",
            "docnm_kwd": "Doc Bad Type",
            "content_with_weight": "body-bad-type",
            "question_kwd": [],
            "q_vec": {"bad": "type"},
            "page_num_int": 1,
            "position_int": 2,
            "top_int": 2,
        },
        "chunk-low-zero": {
            "doc_id": "doc-low-zero",
            "docnm_kwd": "Doc Low Zero",
            "content_with_weight": "body-low",
            "question_kwd": [],
            "q_vec": "0\t0",
            "page_num_int": 1,
            "position_int": 3,
            "top_int": 3,
        },
        "chunk-no-text": {
            "doc_id": "doc-no-text",
            "docnm_kwd": "Doc No Text",
            "content_with_weight": "TRIGGER_NO_TEXT",
            "q_vec": [1.0, 0.0],
            "page_num_int": 1,
            "position_int": 4,
            "top_int": 4,
        },
        "chunk-mix": {
            "doc_id": "doc-mix",
            "docnm_kwd": "Doc Mix",
            "content_with_weight": "body-mix",
            "q_vec": [1.0, 0.0],
            "page_num_int": 1,
            "position_int": 5,
            "top_int": 5,
        },
    }

    monkeypatch.setattr(
        module.settings,
        "docStoreConn",
        _DocStore(
            total=6,
            ids_by_offset={
                0: [],
                1: ["chunk-no-vec"],
                2: ["chunk-bad-type"],
                3: ["chunk-low-zero"],
                4: ["chunk-no-text"],
                5: ["chunk-mix"],
            },
            docs=low_docs,
        ),
    )

    _set_request_json(monkeypatch, module, {"kb_id": "kb-1", "embd_id": "emb-1", "check_num": 6})
    res = _run(route())
    assert res["code"] == module.RetCode.NOT_EFFECTIVE, res
    assert "average similarity" in res["message"], res
    summary = res["data"]["summary"]
    assert summary["sampled"] == 5, summary
    assert summary["valid"] == 2, summary
    reasons = {item.get("reason") for item in res["data"]["results"] if "reason" in item}
    assert "no_stored_vector" in reasons, res
    assert "no_text" in reasons, res
    assert any(item.get("chunk_id") == "chunk-low-zero" and "cos_sim" in item for item in res["data"]["results"]), res
    assert summary["match_mode"] in {"content_only", "title+content"}, summary

    high_docs = {
        "chunk-high": {
            "doc_id": "doc-high",
            "docnm_kwd": "Doc High",
            "content_with_weight": "body-high",
            "q_vec": [1.0, 0.0],
            "page_num_int": 1,
            "position_int": 1,
            "top_int": 1,
        }
    }
    monkeypatch.setattr(
        module.settings,
        "docStoreConn",
        _DocStore(total=1, ids_by_offset={0: ["chunk-high"]}, docs=high_docs),
    )
    _set_request_json(monkeypatch, module, {"kb_id": "kb-1", "embd_id": "emb-1", "check_num": 1})
    res = _run(route())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["summary"]["avg_cos_sim"] > 0.9, res
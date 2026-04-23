async def check_embedding():

    def _guess_vec_field(src: dict) -> str | None:
        for k in src or {}:
            if k.endswith("_vec"):
                return k
        return None

    def _as_float_vec(v):
        if v is None:
            return []
        if isinstance(v, str):
            return [float(x) for x in v.split("\t") if x != ""]
        if isinstance(v, (list, tuple, np.ndarray)):
            return [float(x) for x in v]
        return []

    def _to_1d(x):
        a = np.asarray(x, dtype=np.float32)
        return a.reshape(-1)

    def _cos_sim(a, b, eps=1e-12):
        a = _to_1d(a)
        b = _to_1d(b)
        na = np.linalg.norm(a)
        nb = np.linalg.norm(b)
        if na < eps or nb < eps:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def sample_random_chunks_with_vectors(
        docStoreConn,
        tenant_id: str,
        kb_id: str,
        n: int = 5,
        base_fields=("docnm_kwd","doc_id","content_with_weight","page_num_int","position_int","top_int"),
    ):
        index_nm = search.index_name(tenant_id)

        res0 = docStoreConn.search(
            select_fields=[], highlight_fields=[],
            condition={"kb_id": kb_id, "available_int": 1},
            match_expressions=[], order_by=OrderByExpr(),
            offset=0, limit=1,
            index_names=index_nm, knowledgebase_ids=[kb_id]
        )
        total = docStoreConn.get_total(res0)
        if total <= 0:
            return []

        n = min(n, total)
        offsets = sorted(random.sample(range(min(total,1000)), n))
        out = []

        for off in offsets:
            res1 = docStoreConn.search(
                select_fields=list(base_fields),
                highlight_fields=[],
                condition={"kb_id": kb_id, "available_int": 1},
                match_expressions=[], order_by=OrderByExpr(),
                offset=off, limit=1,
                index_names=index_nm, knowledgebase_ids=[kb_id]
            )
            ids = docStoreConn.get_doc_ids(res1)
            if not ids:
                continue

            cid = ids[0]
            full_doc = docStoreConn.get(cid, index_nm, [kb_id]) or {}
            vec_field = _guess_vec_field(full_doc)
            vec = _as_float_vec(full_doc.get(vec_field))

            out.append({
                "chunk_id": cid,
                "kb_id": kb_id,
                "doc_id": full_doc.get("doc_id"),
                "doc_name": full_doc.get("docnm_kwd"),
                "vector_field": vec_field,
                "vector_dim": len(vec),
                "vector": vec,
                "page_num_int": full_doc.get("page_num_int"),
                "position_int": full_doc.get("position_int"),
                "top_int": full_doc.get("top_int"),
                "content_with_weight": full_doc.get("content_with_weight") or "",
                "question_kwd": full_doc.get("question_kwd") or []
            })
        return out

    def _clean(s: str) -> str:
        s = re.sub(r"</?(table|td|caption|tr|th)( [^<>]{0,12})?>", " ", s or "")
        return s if s else "None"
    req = await get_request_json()
    kb_id = req.get("kb_id", "")
    tenant_embd_id = req.get("tenant_embd_id")
    embd_id = req.get("embd_id", "")
    n = int(req.get("check_num", 5))
    _, kb = KnowledgebaseService.get_by_id(kb_id)
    tenant_id = kb.tenant_id
    if tenant_embd_id:
        embd_model_config = get_model_config_by_id(tenant_embd_id)
    elif embd_id:
        embd_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING, embd_id)
    else:
        return get_error_data_result("`tenant_embd_id` or `embd_id` is required.")
    emb_mdl = LLMBundle(tenant_id, embd_model_config)
    samples = sample_random_chunks_with_vectors(settings.docStoreConn, tenant_id=tenant_id, kb_id=kb_id, n=n)

    results, eff_sims = [], []
    for ck in samples:
        title = ck.get("doc_name") or "Title"
        txt_in = "\n".join(ck.get("question_kwd") or []) or ck.get("content_with_weight") or ""
        txt_in = _clean(txt_in)
        if not txt_in:
            results.append({"chunk_id": ck["chunk_id"], "reason": "no_text"})
            continue

        if not ck.get("vector"):
            results.append({"chunk_id": ck["chunk_id"], "reason": "no_stored_vector"})
            continue

        try:
            v, _ = emb_mdl.encode([title, txt_in])
            assert len(v[1]) == len(ck["vector"]), f"The dimension ({len(v[1])}) of given embedding model is different from the original ({len(ck['vector'])})"
            sim_content = _cos_sim(v[1], ck["vector"])
            title_w = 0.1
            qv_mix = title_w * v[0] + (1 - title_w) * v[1]
            sim_mix = _cos_sim(qv_mix, ck["vector"])
            sim = sim_content
            mode = "content_only"
            if sim_mix > sim:
                sim = sim_mix
                mode = "title+content"
        except Exception as e:
            return get_error_data_result(message=f"Embedding failure. {e}")

        eff_sims.append(sim)
        results.append({
            "chunk_id": ck["chunk_id"],
            "doc_id": ck["doc_id"],
            "doc_name": ck["doc_name"],
            "vector_field": ck["vector_field"],
            "vector_dim": ck["vector_dim"],
            "cos_sim": round(sim, 6),
        })

    summary = {
        "kb_id": kb_id,
        "model": embd_id,
        "sampled": len(samples),
        "valid": len(eff_sims),
        "avg_cos_sim": round(float(np.mean(eff_sims)) if eff_sims else 0.0, 6),
        "min_cos_sim": round(float(np.min(eff_sims)) if eff_sims else 0.0, 6),
        "max_cos_sim": round(float(np.max(eff_sims)) if eff_sims else 0.0, 6),
        "match_mode": mode,
    }
    if summary["avg_cos_sim"] > 0.9:
        return get_json_result(data={"summary": summary, "results": results})
    return get_json_result(code=RetCode.NOT_EFFECTIVE, message="Embedding model switch failed: the average similarity between old and new vectors is below 0.9, indicating incompatible vector spaces.", data={"summary": summary, "results": results})
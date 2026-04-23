def _ensure_model_provider_ready_via_api(base_url: str, auth_header: str) -> dict:
    headers = {"Authorization": auth_header}

    _, my_llms_payload = _api_request_json(
        _build_url(base_url, "/v1/llm/my_llms"), headers=headers
    )
    my_llms_data = _response_data(my_llms_payload)
    has_provider = bool(my_llms_data)
    created_provider = False
    zhipu_key = os.getenv("ZHIPU_AI_API_KEY")

    if not has_provider and zhipu_key:
        _, set_key_payload = _api_request_json(
            _build_url(base_url, "/v1/llm/set_api_key"),
            method="POST",
            payload={"llm_factory": "ZHIPU-AI", "api_key": zhipu_key},
            headers=headers,
        )
        _response_data(set_key_payload)
        has_provider = True
        created_provider = True
        _, my_llms_payload = _api_request_json(
            _build_url(base_url, "/v1/llm/my_llms"), headers=headers
        )
        my_llms_data = _response_data(my_llms_payload)

    if not has_provider:
        pytest.skip("No model provider configured and ZHIPU_AI_API_KEY is not set.")

    _, tenant_payload = _api_request_json(
        _build_url(base_url, "/v1/user/tenant_info"), headers=headers
    )
    tenant_data = _response_data(tenant_payload)
    tenant_id = tenant_data.get("tenant_id")
    if not tenant_id:
        raise RuntimeError(f"tenant_info missing tenant_id: {tenant_data}")

    current_llm = str(tenant_data.get("llm_id") or "").strip()
    current_embd = str(tenant_data.get("embd_id") or "").strip()
    current_img2txt = str(tenant_data.get("img2txt_id") or "").strip()
    current_asr = str(tenant_data.get("asr_id") or "").strip()
    current_rerank = str(tenant_data.get("rerank_id") or "").strip()
    current_tts = str(tenant_data.get("tts_id") or "").strip()

    target_llm = current_llm
    if not target_llm or _is_malformed_tenant_model_value(target_llm):
        target_llm = _normalize_tenant_model_value(current_llm)
        if not target_llm and _provider_has_model(my_llms_data, "ZHIPU-AI", "glm-4-flash"):
            target_llm = "glm-4-flash@ZHIPU-AI"
    if not target_llm:
        pytest.skip(
            "Provider exists but no canonical default llm_id could be inferred for tenant setup."
        )

    target_embd = current_embd
    if not target_embd or _is_malformed_tenant_model_value(target_embd):
        target_embd = _normalize_tenant_model_value(current_embd)
        if not target_embd and _provider_has_model(my_llms_data, "ZHIPU-AI", "embedding-2"):
            target_embd = "embedding-2@ZHIPU-AI"
        if not target_embd:
            target_embd = "BAAI/bge-small-en-v1.5@Builtin"

    target_img2txt = current_img2txt
    if _is_malformed_tenant_model_value(target_img2txt):
        target_img2txt = _normalize_tenant_model_value(current_img2txt)
        if not target_img2txt and _provider_has_model(my_llms_data, "ZHIPU-AI", "glm-4.5v"):
            target_img2txt = "glm-4.5v@ZHIPU-AI"
    target_img2txt = target_img2txt or ""

    target_asr = current_asr
    if _is_malformed_tenant_model_value(target_asr):
        target_asr = _normalize_tenant_model_value(current_asr)
        if not target_asr and _provider_has_model(my_llms_data, "ZHIPU-AI", "glm-asr"):
            target_asr = "glm-asr@ZHIPU-AI"
    target_asr = target_asr or ""

    target_rerank = current_rerank
    if _is_malformed_tenant_model_value(target_rerank):
        target_rerank = _normalize_tenant_model_value(current_rerank)
    target_rerank = target_rerank or ""

    target_tts = current_tts
    if _is_malformed_tenant_model_value(target_tts):
        target_tts = _normalize_tenant_model_value(current_tts)
    target_tts = target_tts or ""

    should_update_tenant_defaults = (
        target_llm != current_llm
        or target_embd != current_embd
        or target_img2txt != current_img2txt
        or target_asr != current_asr
        or target_rerank != current_rerank
        or target_tts != current_tts
    )

    if should_update_tenant_defaults:
        tenant_payload = {
            "tenant_id": tenant_id,
            "llm_id": target_llm,
            "embd_id": target_embd,
            "img2txt_id": target_img2txt,
            "asr_id": target_asr,
            "rerank_id": target_rerank,
            "tts_id": target_tts,
        }
        _, set_tenant_payload = _api_request_json(
            _build_url(base_url, "/v1/user/set_tenant_info"),
            method="POST",
            payload=tenant_payload,
            headers=headers,
        )
        _response_data(set_tenant_payload)

    return {
        "tenant_id": tenant_id,
        "has_provider": True,
        "created_provider": created_provider,
        "normalized_defaults": should_update_tenant_defaults,
        "llm_factories": list(my_llms_data.keys()) if isinstance(my_llms_data, dict) else [],
    }
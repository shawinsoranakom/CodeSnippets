def ensure_tenant_model_id_for_params(tenant_id: str, param_dict: dict, *, strict: bool = False) -> dict:
    for key in ["llm_id", "embd_id", "asr_id", "img2txt_id", "rerank_id", "tts_id"]:
        if param_dict.get(key) and not param_dict.get(f"tenant_{key}"):
            model_type = _KEY_TO_MODEL_TYPE.get(key)
            tenant_model = TenantLLMService.get_api_key(tenant_id, param_dict[key], model_type)
            if not tenant_model and model_type == LLMType.CHAT:
                tenant_model = TenantLLMService.get_api_key(tenant_id, param_dict[key])
            if tenant_model:
                param_dict.update({f"tenant_{key}": tenant_model.id})
            else:
                if strict:
                    model_type_val = model_type.value if hasattr(model_type, "value") else model_type
                    raise ArgumentException(
                        f"Tenant Model with name {param_dict[key]} and type {model_type_val} not found"
                    )
                param_dict.update({f"tenant_{key}": 0})
    return param_dict
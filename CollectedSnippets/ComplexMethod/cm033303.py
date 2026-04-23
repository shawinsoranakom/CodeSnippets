def get_tenant_default_model_by_type(tenant_id: str, model_type: str|enum.Enum):
    exist, tenant = TenantService.get_by_id(tenant_id)
    if not exist:
        raise LookupError("Tenant not found")
    model_type_val = model_type if isinstance(model_type, str) else model_type.value
    model_name: str = ""
    match model_type_val:
        case LLMType.EMBEDDING.value:
            model_name = tenant.embd_id
        case LLMType.SPEECH2TEXT.value:
            model_name =  tenant.asr_id
        case LLMType.IMAGE2TEXT.value:
            model_name = tenant.img2txt_id
        case LLMType.CHAT.value:
            model_name = tenant.llm_id
        case LLMType.RERANK.value:
            model_name = tenant.rerank_id
        case LLMType.TTS.value:
            model_name = tenant.tts_id
        case LLMType.OCR.value:
            raise Exception("OCR model name is required")
        case _:
            raise Exception(f"Unknown model type {model_type}")
    if not model_name:
        raise Exception(f"No default {model_type} model is set.")
    return get_model_config_by_type_and_name(tenant_id, model_type, model_name)
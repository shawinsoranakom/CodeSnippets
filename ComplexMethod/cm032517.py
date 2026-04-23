def _get_tenant_default_model_by_type(tenant_id: str, model_type):
        # Check if tenant exists
        from api.db.services.tenant_llm_service import TenantService
        exist, tenant = TenantService.get_by_id(tenant_id)
        if not exist:
            raise LookupError("Tenant not found!")
        # Return mock tenant with default model configurations
        model_type_val = model_type if isinstance(model_type, str) else model_type.value
        model_name = ""
        if model_type_val == "embedding":
            model_name = tenant.embd_id
        elif model_type_val == "speech2text":
            model_name = tenant.asr_id
        elif model_type_val == "image2text":
            model_name = tenant.img2txt_id
        elif model_type_val == "chat":
            model_name = tenant.llm_id
        elif model_type_val == "rerank":
            model_name = tenant.rerank_id
        elif model_type_val == "tts":
            model_name = tenant.tts_id
        elif model_type_val == "ocr":
            raise Exception("OCR model name is required")
        if not model_name:
            # Use friendly model type names
            friendly_names = {
                "embedding": "Embedding",
                "speech2text": "ASR",
                "image2text": "Image2Text",
                "chat": "Chat",
                "rerank": "Rerank",
                "tts": "TTS",
                "ocr": "OCR"
            }
            friendly_name = friendly_names.get(model_type_val, model_type_val)
            raise Exception(f"No default {friendly_name} model is set")
        return _MockModelConfig2(tenant_id, model_name, model_type_val).to_dict()
def get_model_config_by_type_and_name(tenant_id: str, model_type: str, model_name: str):
    if not model_name:
        raise Exception("Model Name is required")
    model_type_val = model_type.value if hasattr(model_type, "value") else model_type
    model_config = TenantLLMService.get_api_key(tenant_id, model_name, model_type_val)
    if not model_config:
        # model_name in format 'name@factory', split model_name and try again
        pure_model_name, fid = TenantLLMService.split_model_name_and_factory(model_name)
        compose_profiles = os.getenv("COMPOSE_PROFILES", "")
        is_tei_builtin_embedding = (
            model_type_val == LLMType.EMBEDDING.value
            and "tei-" in compose_profiles
            and pure_model_name == os.getenv("TEI_MODEL", "")
            and (fid == "Builtin" or fid is None)
        )
        if is_tei_builtin_embedding:
            # configured local embedding model
            embedding_cfg = settings.EMBEDDING_CFG
            config_dict = {
                "llm_factory": "Builtin",
                "api_key": embedding_cfg["api_key"],
                "llm_name": pure_model_name,
                "api_base": embedding_cfg["base_url"],
                "model_type": LLMType.EMBEDDING.value,
            }
        else:
            model_config = TenantLLMService.get_api_key(tenant_id, pure_model_name, model_type_val)
            if not model_config:
                raise LookupError(f"Tenant Model with name {model_name} and type {model_type_val} not found")
            config_dict = model_config.to_dict()
    else:
        # model_name without @factory
        config_dict = model_config.to_dict()
    config_model_type = config_dict.get("model_type")
    config_model_type = config_model_type.value if hasattr(config_model_type, "value") else config_model_type
    if config_model_type != model_type_val:
        raise LookupError(
            f"Tenant Model with name {model_name} has type {config_model_type}, expected {model_type_val}"
        )
    llm = LLMService.query(llm_name=config_dict["llm_name"])
    if llm:
        config_dict["is_tools"] = llm[0].is_tools
    return config_dict
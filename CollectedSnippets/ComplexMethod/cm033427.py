def verify_embedding_availability(embd_id: str, tenant_id: str) -> tuple[bool, str | None]:
    from api.db.services.llm_service import LLMService
    from api.db.services.tenant_llm_service import TenantLLMService

    """
    Verifies availability of an embedding model for a specific tenant.

    Performs comprehensive verification through:
    1. Identifier Parsing: Decomposes embd_id into name and factory components
    2. System Verification: Checks model registration in LLMService
    3. Tenant Authorization: Validates tenant-specific model assignments
    4. Built-in Model Check: Confirms inclusion in predefined system models

    Args:
        embd_id (str): Unique identifier for the embedding model in format "model_name@factory"
        tenant_id (str): Tenant identifier for access control

    Returns:
        tuple[bool, Response | None]:
        - First element (bool):
            - True: Model is available and authorized
            - False: Validation failed
        - Second element contains:
            - None on success
            - Error detail dict on failure

    Raises:
        ValueError: When model identifier format is invalid
        OperationalError: When database connection fails (auto-handled)

    Examples:
        >>> verify_embedding_availability("text-embedding@openai", "tenant_123")
        (True, None)

        >>> verify_embedding_availability("invalid_model", "tenant_123")
        (False, {'code': 101, 'message': "Unsupported model: <invalid_model>"})
    """
    try:
        llm_name, llm_factory = TenantLLMService.split_model_name_and_factory(embd_id)
        in_llm_service = bool(LLMService.query(llm_name=llm_name, fid=llm_factory, model_type="embedding"))

        tenant_llms = TenantLLMService.get_my_llms(tenant_id=tenant_id)
        is_tenant_model = any(llm["llm_name"] == llm_name and llm["llm_factory"] == llm_factory and llm["model_type"] == "embedding" for llm in tenant_llms)

        is_builtin_model = llm_factory == "Builtin"
        if not (is_builtin_model or is_tenant_model or in_llm_service):
            return False, f"Unsupported model: <{embd_id}>"

        if not (is_builtin_model or is_tenant_model):
            return False, f"Unauthorized model: <{embd_id}>"
    except OperationalError as e:
        logging.exception(e)
        return False, "Database operation failed"
    except Exception as e:
        logging.exception(e)
        return False, "Internal server error"

    return True, None
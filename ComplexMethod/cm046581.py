def _inject_local_providers(recipe: dict[str, Any], request: Request) -> None:
    """
    Mutate recipe dict in-place: for any provider with is_local=True,
    generate a JWT and fill in the endpoint pointing at this server.
    """
    providers = recipe.get("model_providers")
    if not providers:
        return

    # Collect local providers and pop is_local from ALL dicts unconditionally.
    # Strict `is True` guard so malformed payloads (is_local: 1,
    # is_local: "true") do not accidentally trigger the loopback rewrite.
    local_indices: list[int] = []
    for i, provider in enumerate(providers):
        if not isinstance(provider, dict):
            continue
        is_local = provider.pop("is_local", None)
        if is_local is True:
            local_indices.append(i)

    if not local_indices:
        return

    endpoint = _resolve_local_v1_endpoint(request)

    # Only gate on model-loaded if a local provider is actually reachable
    # from an LLM column through a model_config. Orphan model_config nodes
    # that reference a local provider but that no LLM column uses should
    # not block runs; the recipe would never call /v1 for them.
    local_names = {
        providers[i].get("name") for i in local_indices if providers[i].get("name")
    }
    used_aliases = _used_llm_model_aliases(recipe)
    referenced_providers = {
        mc.get("provider")
        for mc in recipe.get("model_configs", [])
        if (
            isinstance(mc, dict)
            and mc.get("provider")
            and mc.get("alias") in used_aliases
        )
    }

    token = ""
    if local_names & referenced_providers:
        # Verify a model is loaded.
        # NOTE: This is a point-in-time check (TOCTOU). The model could be unloaded
        # or swapped after this check but before the recipe subprocess calls /v1.
        # The inference endpoint returns a clear 400 in that case.
        #
        # Imports are deferred to avoid circular dependencies with inference modules.
        from routes.inference import get_llama_cpp_backend
        from core.inference import get_inference_backend

        llama = get_llama_cpp_backend()
        model_loaded = llama.is_loaded
        if not model_loaded:
            backend = get_inference_backend()
            model_loaded = bool(backend.active_model_name)
        if not model_loaded:
            raise ValueError(
                "No model loaded in Chat. Load a model first, then run the recipe."
            )

        from auth.authentication import (
            create_access_token,
        )  # deferred: avoids circular import

        # Uses the "unsloth" admin subject. If the user changes their password,
        # the JWT secret rotates and this token becomes invalid mid-run.
        # Acceptable for v1 - recipes typically finish well within one session.
        token = create_access_token(
            subject = "unsloth",
            expires_delta = timedelta(hours = 24),
        )

    # Defensively strip any stale "external"-only fields the frontend may
    # have left on the dict (extra_headers/extra_body/api_key_env). The UI
    # hides these inputs in local mode but the payload builder still serializes
    # them, so a previously external provider that flipped to local can carry
    # invalid JSON or rogue auth headers into the local /v1 call.
    for i in local_indices:
        providers[i]["endpoint"] = endpoint
        providers[i]["api_key"] = token
        providers[i]["provider_type"] = "openai"
        providers[i].pop("api_key_env", None)
        providers[i].pop("extra_headers", None)
        providers[i].pop("extra_body", None)

    # Force skip_health_check on any model_config that references a local
    # provider. The local /v1/models endpoint only lists the real loaded
    # model (e.g. "unsloth/llama-3.2-1b") and not the placeholder "local"
    # that the recipe sends as the model id, so data_designer's pre-flight
    # health check would otherwise fail before the first completion call.
    # The backend route ignores the model id field in chat completions, so
    # skipping the check is safe.
    for mc in recipe.get("model_configs", []):
        if not isinstance(mc, dict):
            continue
        if mc.get("provider") in local_names:
            mc["skip_health_check"] = True
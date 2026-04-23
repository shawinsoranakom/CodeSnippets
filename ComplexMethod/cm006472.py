async def custom_component_update(
    code_request: UpdateCustomComponentRequest,
    user: CurrentActiveUser,
):
    """Update an existing custom component with new code and configuration.

    Processes the provided code and template updates, applies parameter changes (including those loaded from the
    database), updates the component's build configuration, and validates outputs. Returns the updated component node as
    a JSON-serializable dictionary.

    Raises:
        HTTPException: If an error occurs during component building or updating.
        SerializationError: If serialization of the updated component node fails.
    """
    settings_service = get_settings_service()
    if not settings_service.settings.allow_custom_components:
        get_component_hash_lookups_for_validation()
        all_known = component_cache.all_known_hashes
        if all_known is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Component templates are still initializing. Please try again in a few seconds.",
            )
        if not code_hash_matches_any_template(code_request.code, all_known):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Custom component creation is disabled",
            )

    try:
        component = Component(_code=code_request.code)
        component_node, cc_instance = build_custom_component_template(
            component,
            user_id=user.id,
        )

        component_node["tool_mode"] = code_request.tool_mode

        if hasattr(cc_instance, "set_attributes"):
            template = code_request.get_template()
            params = {}

            for key, value_dict in template.items():
                if isinstance(value_dict, dict):
                    value = value_dict.get("value")
                    input_type = str(value_dict.get("_input_type"))
                    params[key] = parse_value(value, input_type)

            load_from_db_fields = [
                field_name
                for field_name, field_dict in template.items()
                if isinstance(field_dict, dict) and field_dict.get("load_from_db") and field_dict.get("value")
            ]
            if isinstance(cc_instance, Component):
                # ``fallback_to_env_vars=True`` so a missing variable (e.g. an
                # imported flow referencing ``ANTHROPIC_API_KEY`` when the
                # current user hasn't configured one) degrades to ``None``
                # instead of raising.  This endpoint only refreshes form
                # metadata — it does not execute the component — so we don't
                # need the real credential here.  The runtime build path still
                # calls ``update_params_with_load_from_db_fields`` with its own
                # fallback setting, so this change doesn't relax execution-time
                # requirements.
                params = await update_params_with_load_from_db_fields(
                    cc_instance,
                    params,
                    load_from_db_fields,
                    fallback_to_env_vars=True,
                )
                cc_instance.set_attributes(params)
        updated_build_config = code_request.get_template()
        await update_component_build_config(
            cc_instance,
            build_config=updated_build_config,
            field_value=code_request.field_value,
            field_name=code_request.field,
        )
        if "code" not in updated_build_config or not updated_build_config.get("code", {}).get("value"):
            updated_build_config = add_code_field_to_build_config(updated_build_config, code_request.code)
        component_node["template"] = updated_build_config

        if isinstance(cc_instance, Component):
            await cc_instance.run_and_validate_update_outputs(
                frontend_node=component_node,
                field_name=code_request.field,
                field_value=code_request.field_value,
            )

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return jsonable_encoder(component_node)
    except Exception as exc:
        raise SerializationError.from_exception(exc, data=component_node) from exc
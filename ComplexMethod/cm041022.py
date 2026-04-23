def resolve_resource_parameters(
    account_id_: str,
    region_name_: str,
    stack_name: str,
    resource_definition: ResourceDefinition,
    resources: dict[str, ResourceDefinition],
    resource_id: str,
    func_details: FuncDetailsValue,
) -> dict | None:
    params = func_details.get("parameters") or (
        lambda account_id, region_name, properties, logical_resource_id, *args, **kwargs: properties
    )
    resource_props = resource_definition["Properties"] = resource_definition.get("Properties", {})
    resource_props = dict(resource_props)
    resource_state = resource_definition.get(KEY_RESOURCE_STATE, {})
    last_deployed_state = resource_definition.get("_last_deployed_state", {})

    if callable(params):
        # resolve parameter map via custom function
        params = params(
            account_id_, region_name_, resource_props, resource_id, resource_definition, stack_name
        )
    else:
        # it could be a list like ['param1', 'param2', {'apiCallParamName': 'cfResourcePropName'}]
        if isinstance(params, list):
            _params = {}
            for param in params:
                if isinstance(param, dict):
                    _params.update(param)
                else:
                    _params[param] = param
            params = _params

        params = dict(params)
        # TODO(srw): mutably mapping params :(
        for param_key, prop_keys in dict(params).items():
            params.pop(param_key, None)
            if not isinstance(prop_keys, list):
                prop_keys = [prop_keys]
            for prop_key in prop_keys:
                if callable(prop_key):
                    prop_value = prop_key(
                        account_id_,
                        region_name_,
                        resource_props,
                        resource_id,
                        resource_definition,
                        stack_name,
                    )
                else:
                    prop_value = resource_props.get(
                        prop_key,
                        resource_definition.get(
                            prop_key,
                            resource_state.get(prop_key, last_deployed_state.get(prop_key)),
                        ),
                    )
                if prop_value is not None:
                    params[param_key] = prop_value
                    break

    # this is an indicator that we should skip this resource deployment, and return
    if params is None:
        return

    # FIXME: move this to a single place after template processing is finished
    # convert any moto account IDs (123456789012) in ARNs to our format (000000000000)
    params = fix_account_id_in_arns(params, account_id_)
    # convert data types (e.g., boolean strings to bool)
    # TODO: this might not be needed anymore
    params = convert_data_types(func_details.get("types", {}), params)
    # remove None values, as they usually raise boto3 errors
    params = remove_none_values(params)

    return params
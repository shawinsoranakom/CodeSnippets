def resolve_parameters(
    account_id: str,
    region_name: str,
    parameter_declarations: dict[str, ParameterDeclaration],
    new_parameters: dict[str, Parameter],
    old_parameters: dict[str, Parameter],
) -> dict[str, StackParameter]:
    """
    Resolves stack parameters or raises an exception if any parameter can not be resolved.

    Assumptions:
        - There are no extra undeclared parameters given (validate before calling this method)

    TODO: is UsePreviousValue=False equivalent to not specifying it, in all situations?

    :param parameter_declarations: The parameter declaration from the (potentially new) template, i.e. the "Parameters" section
    :param new_parameters: The parameters to resolve
    :param old_parameters: The old parameters from the previous stack deployment, if available
    :return: a copy of new_parameters with resolved values
    """
    resolved_parameters = {}

    # populate values for every parameter declared in the template
    for pm in parameter_declarations.values():
        pm_key = pm["ParameterKey"]
        resolved_param = StackParameter(ParameterKey=pm_key, ParameterType=pm["ParameterType"])
        new_parameter = new_parameters.get(pm_key)
        old_parameter = old_parameters.get(pm_key)

        if new_parameter is None:
            # since no value has been specified for the deployment, we need to be able to resolve the default or fail
            default_value = pm["DefaultValue"]
            if default_value is None:
                LOG.error("New parameter without a default value: %s", pm_key)
                raise Exception(
                    f"Invalid. Parameter '{pm_key}' needs to have either param specified or Default."
                )  # TODO: test and verify

            resolved_param["ParameterValue"] = default_value
        else:
            if (
                new_parameter.get("UsePreviousValue", False)
                and new_parameter.get("ParameterValue") is not None
            ):
                raise Exception(
                    f"Can't set both 'UsePreviousValue' and a concrete value for parameter '{pm_key}'."
                )  # TODO: test and verify

            if new_parameter.get("UsePreviousValue", False):
                if old_parameter is None:
                    raise Exception(
                        f"Set 'UsePreviousValue' but stack has no previous value for parameter '{pm_key}'."
                    )  # TODO: test and verify

                resolved_param["ParameterValue"] = old_parameter["ParameterValue"]
            else:
                resolved_param["ParameterValue"] = new_parameter["ParameterValue"]

        resolved_param["NoEcho"] = pm.get("NoEcho", False)
        resolved_parameters[pm_key] = resolved_param

        # Note that SSM parameters always need to be resolved anew here
        # TODO: support more parameter types
        if pm["ParameterType"].startswith("AWS::SSM"):
            if pm["ParameterType"] in [
                "AWS::SSM::Parameter::Value<String>",
                "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>",
                "AWS::SSM::Parameter::Value<CommaDelimitedList>",
            ]:
                # TODO: error handling (e.g. no permission to lookup SSM parameter or SSM parameter doesn't exist)
                resolved_param["ResolvedValue"] = resolve_ssm_parameter(
                    account_id, region_name, resolved_param["ParameterValue"]
                )
            else:
                raise Exception(f"Unsupported stack parameter type: {pm['ParameterType']}")

    return resolved_parameters
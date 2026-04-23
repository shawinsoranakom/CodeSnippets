def _resolve_parameters(
        template: dict | None,
        parameters: dict | None,
        account_id: str,
        region_name: str,
        before_parameters: dict | None,
    ) -> dict[str, EngineParameter]:
        template_parameters = template.get("Parameters", {})
        resolved_parameters = {}
        invalid_parameters = []
        for name, parameter in template_parameters.items():
            given_value = parameters.get(name)
            default_value = parameter.get("Default")
            resolved_parameter = EngineParameter(
                type_=parameter["Type"],
                given_value=given_value,
                default_value=default_value,
                no_echo=parameter.get("NoEcho"),
            )

            # validate the type
            if parameter["Type"] == "Number" and not is_number(
                engine_parameter_value(resolved_parameter)
            ):
                raise ValidationError(f"Parameter '{name}' must be a number.")

            # TODO: support other parameter types
            if match := SSM_PARAMETER_TYPE_RE.match(parameter["Type"]):
                inner_type = match.group("innertype")
                is_list_type = match.group("listtype") is not None
                if is_list_type or inner_type == "CommaDelimitedList":
                    # list types
                    try:
                        resolved_value = resolve_ssm_parameter(
                            account_id, region_name, given_value or default_value
                        )
                        resolved_parameter["resolved_value"] = resolved_value.split(",")
                    except Exception:
                        raise ValidationError(
                            f"Parameter {name} should either have input value or default value"
                        )
                else:
                    try:
                        resolved_parameter["resolved_value"] = resolve_ssm_parameter(
                            account_id, region_name, given_value or default_value
                        )
                    except Exception as e:
                        # we could not find the parameter however CDK provides the resolved value rather than the
                        # parameter name again so try to look up the value in the previous parameters
                        if (
                            before_parameters
                            and (before_param := before_parameters.get(name))
                            and isinstance(before_param, dict)
                            and (resolved_value := before_param.get("resolved_value"))
                        ):
                            LOG.debug(
                                "Parameter %s could not be resolved, using previous value of %s",
                                name,
                                resolved_value,
                            )
                            resolved_parameter["resolved_value"] = resolved_value
                        else:
                            raise ValidationError(
                                f"Parameter {name} should either have input value or default value"
                            ) from e
            elif given_value is None and default_value is None:
                invalid_parameters.append(name)
                continue

            resolved_parameters[name] = resolved_parameter

        if invalid_parameters:
            raise ValidationError(f"Parameters: [{','.join(invalid_parameters)}] must have values")

        for name, parameter in resolved_parameters.items():
            if (
                parameter.get("resolved_value") is None
                and parameter.get("given_value") is None
                and parameter.get("default_value") is None
            ):
                raise ValidationError(
                    f"Parameter {name} should either have input value or default value"
                )

        return resolved_parameters
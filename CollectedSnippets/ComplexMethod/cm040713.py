def _create_routing_config_model(
        self, routing_config_dict: dict[str, float], function_version: FunctionVersion
    ):
        if len(routing_config_dict) > 1:
            raise InvalidParameterValueException(
                "Number of items in AdditionalVersionWeights cannot be greater than 1",
                Type="User",
            )
        # should be exactly one item here, still iterating, might be supported in the future
        for key, value in routing_config_dict.items():
            if value < 0.0 or value >= 1.0:
                raise ValidationException(
                    f"1 validation error detected: Value '{{{key}={value}}}' at 'routingConfig.additionalVersionWeights' failed to satisfy constraint: Map value must satisfy constraint: [Member must have value less than or equal to 1.0, Member must have value greater than or equal to 0.0, Member must not be null]"
                )
            if key == function_version.id.qualifier:
                raise InvalidParameterValueException(
                    f"Invalid function version {function_version.id.qualifier}. Function version {function_version.id.qualifier} is already included in routing configuration.",
                    Type="User",
                )
            # check if version target is latest, then no routing config is allowed
            if function_version.id.qualifier == "$LATEST":
                raise InvalidParameterValueException(
                    "$LATEST is not supported for an alias pointing to more than 1 version"
                )
            if not api_utils.qualifier_is_version(key):
                raise ValidationException(
                    f"1 validation error detected: Value '{{{key}={value}}}' at 'routingConfig.additionalVersionWeights' failed to satisfy constraint: Map keys must satisfy constraint: [Member must have length less than or equal to 1024, Member must have length greater than or equal to 1, Member must satisfy regular expression pattern: [0-9]+]"
                )

            # checking if the version in the config exists
            get_function_version(
                function_name=function_version.id.function_name,
                qualifier=key,
                region=function_version.id.region,
                account_id=function_version.id.account,
            )
        return AliasRoutingConfig(version_weights=routing_config_dict)
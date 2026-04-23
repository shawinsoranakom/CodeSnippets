def update_alias(
        self,
        context: RequestContext,
        function_name: FunctionName,
        name: Alias,
        function_version: VersionWithLatestPublished = None,
        description: Description = None,
        routing_config: AliasRoutingConfiguration = None,
        revision_id: String = None,
        **kwargs,
    ) -> AliasConfiguration:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name = api_utils.get_function_name(function_name, context)
        function = self._get_function(
            function_name=function_name, region=region, account_id=account_id
        )
        if not (alias := function.aliases.get(name)):
            fn_arn = api_utils.qualified_lambda_arn(function_name, name, account_id, region)
            raise ResourceNotFoundException(
                f"Alias not found: {fn_arn}",
                Type="User",
            )
        if revision_id and alias.revision_id != revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetFunction/GetAlias API to retrieve the latest Revision Id",
                Type="User",
            )
        changes = {}
        if function_version is not None:
            changes |= {"function_version": function_version}
        if description is not None:
            changes |= {"description": description}
        if routing_config is not None:
            # if it is an empty dict or AdditionalVersionWeights is empty, set routing config to None
            new_routing_config = None
            if routing_config_dict := routing_config.get("AdditionalVersionWeights"):
                new_routing_config = self._create_routing_config_model(routing_config_dict)
            changes |= {"routing_configuration": new_routing_config}
        # even if no changes are done, we have to update revision id for some reason
        old_alias = alias
        alias = dataclasses.replace(alias, **changes)
        function.aliases[name] = alias

        # TODO: signal lambda service that pointer potentially changed
        self.lambda_service.update_alias(old_alias=old_alias, new_alias=alias, function=function)

        return api_utils.map_alias_out(alias=alias, function=function)
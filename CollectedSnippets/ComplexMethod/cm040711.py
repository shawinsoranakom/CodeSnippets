def get_function(
        self,
        context: RequestContext,
        function_name: NamespacedFunctionName,
        qualifier: NumericLatestPublishedOrAliasQualifier | None = None,
        **kwargs,
    ) -> GetFunctionResponse:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )

        fn = lambda_stores[account_id][region].functions.get(function_name)
        if fn is None:
            if qualifier is None:
                raise ResourceNotFoundException(
                    f"Function not found: {api_utils.unqualified_lambda_arn(function_name, account_id, region)}",
                    Type="User",
                )
            else:
                raise ResourceNotFoundException(
                    f"Function not found: {api_utils.qualified_lambda_arn(function_name, qualifier, account_id, region)}",
                    Type="User",
                )
        alias_name = None
        if qualifier and api_utils.qualifier_is_alias(qualifier):
            if qualifier not in fn.aliases:
                alias_arn = api_utils.qualified_lambda_arn(
                    function_name, qualifier, account_id, region
                )
                raise ResourceNotFoundException(f"Function not found: {alias_arn}", Type="User")
            alias_name = qualifier
            qualifier = fn.aliases[alias_name].function_version

        version = get_function_version(
            function_name=function_name,
            qualifier=qualifier,
            account_id=account_id,
            region=region,
        )
        tags = self._get_tags(api_utils.unqualified_lambda_arn(function_name, account_id, region))
        additional_fields = {}
        if tags:
            additional_fields["Tags"] = tags
        code_location = None
        if code := version.config.code:
            code_location = FunctionCodeLocation(
                Location=code.generate_presigned_url(endpoint_url=config.external_service_url()),
                RepositoryType="S3",
            )
        elif image := version.config.image:
            code_location = FunctionCodeLocation(
                ImageUri=image.image_uri,
                RepositoryType=image.repository_type,
                ResolvedImageUri=image.resolved_image_uri,
            )
        concurrency = None
        if fn.reserved_concurrent_executions:
            concurrency = Concurrency(
                ReservedConcurrentExecutions=fn.reserved_concurrent_executions
            )

        return GetFunctionResponse(
            Configuration=api_utils.map_config_out(
                version, return_qualified_arn=bool(qualifier), alias_name=alias_name
            ),
            Code=code_location,  # TODO
            Concurrency=concurrency,
            **additional_fields,
        )
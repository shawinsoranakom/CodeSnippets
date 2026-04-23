def delete_function(
        self,
        context: RequestContext,
        function_name: NamespacedFunctionName,
        qualifier: NumericLatestPublishedOrAliasQualifier | None = None,
        **kwargs,
    ) -> DeleteFunctionResponse:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )

        if qualifier and api_utils.qualifier_is_alias(qualifier):
            raise InvalidParameterValueException(
                "Deletion of aliases is not currently supported.",
                Type="User",
            )

        store = lambda_stores[account_id][region]
        if qualifier == "$LATEST":
            raise InvalidParameterValueException(
                "$LATEST version cannot be deleted without deleting the function.", Type="User"
            )

        unqualified_function_arn = api_utils.unqualified_lambda_arn(
            function_name=function_name, region=region, account=account_id
        )
        if function_name not in store.functions:
            e = ResourceNotFoundException(
                f"Function not found: {unqualified_function_arn}",
                Type="User",
            )
            raise e
        function = store.functions.get(function_name)

        function_has_capacity_provider = False
        if qualifier:
            # delete a version of the function
            version = function.versions.get(qualifier, None)
            if version:
                if version.config.capacity_provider_config:
                    function_has_capacity_provider = True
                    # async delete from store
                    self.lambda_service.delete_function_version_async(function, version, qualifier)
                else:
                    function.versions.pop(qualifier, None)
                self.lambda_service.stop_version(version.id.qualified_arn())
                destroy_code_if_not_used(code=version.config.code, function=function)
        else:
            # delete the whole function
            self._remove_all_tags(unqualified_function_arn)
            # TODO: introduce locking for safe deletion: We could create a new version at the API layer before
            #  the old version gets cleaned up in the internal lambda service.
            function = store.functions.get(function_name)
            if function.latest().config.capacity_provider_config:
                function_has_capacity_provider = True
                # async delete version from store
                self.lambda_service.delete_function_async(store, function_name)

            for version in function.versions.values():
                # Functions with a capacity provider do NOT have a version manager for $LATEST because only
                # published versions are invokable.
                if not function_has_capacity_provider or (
                    function_has_capacity_provider and version.id.qualifier != "$LATEST"
                ):
                    self.lambda_service.stop_version(qualified_arn=version.id.qualified_arn())
                # we can safely destroy the code here
                if version.config.code:
                    version.config.code.destroy()
            if not function_has_capacity_provider:
                store.functions.pop(function_name, None)

        return DeleteFunctionResponse(StatusCode=202 if function_has_capacity_provider else 204)
def list_functions(
        self,
        context: RequestContext,
        master_region: MasterRegion = None,  # (only relevant for lambda@edge)
        function_version: FunctionVersionApi = None,
        marker: String = None,
        max_items: MaxListItems = None,
        **kwargs,
    ) -> ListFunctionsResponse:
        state = lambda_stores[context.account_id][context.region]

        if function_version and function_version != FunctionVersionApi.ALL:
            raise ValidationException(
                f"1 validation error detected: Value '{function_version}'"
                + " at 'functionVersion' failed to satisfy constraint: Member must satisfy enum value set: [ALL]"
            )

        if function_version == FunctionVersionApi.ALL:
            # include all versions for all function
            versions = [v for f in state.functions.values() for v in f.versions.values()]
            return_qualified_arn = True
        else:
            versions = [f.latest() for f in state.functions.values()]
            return_qualified_arn = False

        versions = [
            api_utils.map_to_list_response(
                api_utils.map_config_out(fc, return_qualified_arn=return_qualified_arn)
            )
            for fc in versions
        ]
        versions = PaginatedList(versions)
        page, token = versions.get_page(
            lambda version: version["FunctionArn"],
            marker,
            max_items,
        )
        return ListFunctionsResponse(Functions=page, NextMarker=token)
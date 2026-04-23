def remove_permission(
        self,
        context: RequestContext,
        function_name: NamespacedFunctionName,
        statement_id: NamespacedStatementId,
        qualifier: NumericLatestPublishedOrAliasQualifier | None = None,
        revision_id: String | None = None,
        **kwargs,
    ) -> None:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )
        if qualifier is not None:
            self._validate_qualifier_expression(qualifier)

        state = lambda_stores[account_id][region]
        resolved_fn = state.functions.get(function_name)
        if resolved_fn is None:
            fn_arn = api_utils.unqualified_lambda_arn(function_name, account_id, region)
            raise ResourceNotFoundException(f"No policy found for: {fn_arn}", Type="User")

        resolved_qualifier, _ = self._resolve_fn_qualifier(resolved_fn, qualifier)
        function_permission = resolved_fn.permissions.get(resolved_qualifier)
        if not function_permission:
            raise ResourceNotFoundException(
                "No policy is associated with the given resource.", Type="User"
            )

        # try to find statement in policy and delete it
        statement = None
        for s in function_permission.policy.Statement:
            if s["Sid"] == statement_id:
                statement = s
                break

        if not statement:
            raise ResourceNotFoundException(
                f"Statement {statement_id} is not found in resource policy.", Type="User"
            )
        fn_revision_id = self._function_revision_id(resolved_fn, resolved_qualifier)
        if revision_id and revision_id != fn_revision_id:
            raise PreconditionFailedException(
                "The Revision Id provided does not match the latest Revision Id. "
                "Call the GetFunction/GetAlias API to retrieve the latest Revision Id",
                Type="User",
            )
        function_permission.policy.Statement.remove(statement)

        # Update revision id for alias or version
        # TODO: re-evaluate data model to prevent this dirty hack just for bumping the revision id
        # TODO: does that need a `with function.lock` for atomic updates of the policy + revision_id?
        if api_utils.qualifier_is_alias(resolved_qualifier):
            resolved_alias = resolved_fn.aliases[resolved_qualifier]
            resolved_fn.aliases[resolved_qualifier] = dataclasses.replace(resolved_alias)
        # Assumes that a non-alias is a version
        else:
            resolved_version = resolved_fn.versions[resolved_qualifier]
            resolved_fn.versions[resolved_qualifier] = dataclasses.replace(
                resolved_version, config=dataclasses.replace(resolved_version.config)
            )

        # remove the policy as a whole when there's no statement left in it
        if len(function_permission.policy.Statement) == 0:
            del resolved_fn.permissions[resolved_qualifier]
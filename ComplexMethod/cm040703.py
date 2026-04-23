def _resolve_fn_qualifier(resolved_fn: Function, qualifier: str | None) -> tuple[str, str]:
        """Attempts to resolve a given qualifier and returns a qualifier that exists or
        raises an appropriate ResourceNotFoundException.

        :param resolved_fn: The resolved lambda function
        :param qualifier: The qualifier to be resolved or None
        :return: Tuple of (resolved qualifier, function arn either qualified or unqualified)"""
        function_name = resolved_fn.function_name
        # assuming function versions need to live in the same account and region
        account_id = resolved_fn.latest().id.account
        region = resolved_fn.latest().id.region
        fn_arn = api_utils.unqualified_lambda_arn(function_name, account_id, region)
        if qualifier is not None:
            fn_arn = api_utils.qualified_lambda_arn(function_name, qualifier, account_id, region)
            if api_utils.qualifier_is_alias(qualifier):
                if qualifier not in resolved_fn.aliases:
                    raise ResourceNotFoundException(f"Cannot find alias arn: {fn_arn}", Type="User")
            elif api_utils.qualifier_is_version(qualifier) or qualifier == "$LATEST":
                if qualifier not in resolved_fn.versions:
                    raise ResourceNotFoundException(f"Function not found: {fn_arn}", Type="User")
            else:
                # matches qualifier pattern but invalid alias or version
                raise ResourceNotFoundException(f"Function not found: {fn_arn}", Type="User")
        resolved_qualifier = qualifier or "$LATEST"
        return resolved_qualifier, fn_arn
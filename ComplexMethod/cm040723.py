def put_provisioned_concurrency_config(
        self,
        context: RequestContext,
        function_name: FunctionName,
        qualifier: Qualifier,
        provisioned_concurrent_executions: PositiveInteger,
        **kwargs,
    ) -> PutProvisionedConcurrencyConfigResponse:
        if provisioned_concurrent_executions <= 0:
            raise ValidationException(
                f"1 validation error detected: Value '{provisioned_concurrent_executions}' at 'provisionedConcurrentExecutions' failed to satisfy constraint: Member must have value greater than or equal to 1"
            )

        if qualifier == "$LATEST":
            raise InvalidParameterValueException(
                "Provisioned Concurrency Configs cannot be applied to unpublished function versions.",
                Type="User",
            )
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )
        state = lambda_stores[account_id][region]
        fn = state.functions.get(function_name)

        provisioned_config = self._get_provisioned_config(context, function_name, qualifier)

        if provisioned_config:  # TODO: merge?
            # TODO: add a test for partial updates (if possible)
            LOG.warning(
                "Partial update of provisioned concurrency config is currently not supported."
            )

        other_provisioned_sum = sum(
            [
                provisioned_configs.provisioned_concurrent_executions
                for provisioned_qualifier, provisioned_configs in fn.provisioned_concurrency_configs.items()
                if provisioned_qualifier != qualifier
            ]
        )

        if (
            fn.reserved_concurrent_executions is not None
            and fn.reserved_concurrent_executions
            < other_provisioned_sum + provisioned_concurrent_executions
        ):
            raise InvalidParameterValueException(
                "Requested Provisioned Concurrency should not be greater than the reservedConcurrentExecution for function",
                Type="User",
            )

        if provisioned_concurrent_executions > config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS:
            raise InvalidParameterValueException(
                f"Specified ConcurrentExecutions for function is greater than account's unreserved concurrency"
                f" [{config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS}]."
            )

        settings = self.get_account_settings(context)
        unreserved_concurrent_executions = settings["AccountLimit"][
            "UnreservedConcurrentExecutions"
        ]
        if (
            unreserved_concurrent_executions - provisioned_concurrent_executions
            < config.LAMBDA_LIMITS_MINIMUM_UNRESERVED_CONCURRENCY
        ):
            raise InvalidParameterValueException(
                f"Specified ConcurrentExecutions for function decreases account's UnreservedConcurrentExecution below"
                f" its minimum value of [{config.LAMBDA_LIMITS_MINIMUM_UNRESERVED_CONCURRENCY}]."
            )

        provisioned_config = ProvisionedConcurrencyConfiguration(
            provisioned_concurrent_executions, api_utils.generate_lambda_date()
        )
        fn_arn = api_utils.qualified_lambda_arn(function_name, qualifier, account_id, region)

        if api_utils.qualifier_is_alias(qualifier):
            alias = fn.aliases.get(qualifier)
            resolved_version = fn.versions.get(alias.function_version)

            if (
                resolved_version
                and fn.provisioned_concurrency_configs.get(alias.function_version) is not None
            ):
                raise ResourceConflictException(
                    "Alias can't be used for Provisioned Concurrency configuration on an already Provisioned version",
                    Type="User",
                )
            fn_arn = resolved_version.id.qualified_arn()
        elif api_utils.qualifier_is_version(qualifier):
            fn_version = fn.versions.get(qualifier)

            # TODO: might be useful other places, utilize
            pointing_aliases = []
            for alias in fn.aliases.values():
                if (
                    alias.function_version == qualifier
                    and fn.provisioned_concurrency_configs.get(alias.name) is not None
                ):
                    pointing_aliases.append(alias.name)
            if pointing_aliases:
                raise ResourceConflictException(
                    "Version is pointed by a Provisioned Concurrency alias", Type="User"
                )

            fn_arn = fn_version.id.qualified_arn()

        manager = self.lambda_service.get_lambda_version_manager(fn_arn)

        fn.provisioned_concurrency_configs[qualifier] = provisioned_config

        manager.update_provisioned_concurrency_config(
            provisioned_config.provisioned_concurrent_executions
        )

        return PutProvisionedConcurrencyConfigResponse(
            RequestedProvisionedConcurrentExecutions=provisioned_config.provisioned_concurrent_executions,
            AvailableProvisionedConcurrentExecutions=0,
            AllocatedProvisionedConcurrentExecutions=0,
            Status=ProvisionedConcurrencyStatusEnum.IN_PROGRESS,
            # StatusReason=manager.provisioned_state.status_reason,
            LastModified=provisioned_config.last_modified,  # TODO: does change with configuration or also with state changes?
        )
def get_invocation_lease(
        self,
        function: Function | None,
        function_version: FunctionVersion,
        provisioned_state: ProvisionedConcurrencyState | None = None,
    ) -> Iterator[InitializationType]:
        """An invocation lease reserves the right to schedule an invocation.
        The returned lease type can either be on-demand or provisioned.
        Scheduling preference:
        1) Check for free provisioned concurrency => provisioned
        2) Check for reserved concurrency => on-demand
        3) Check for unreserved concurrency => on-demand

        HACK: We allow the function to be None for Lambda@Edge to skip provisioned and reserved concurrency.
        """
        account = function_version.id.account
        region = function_version.id.region
        scope_tuple = (account, region)
        on_demand_tracker = self.on_demand_concurrency_trackers.get(scope_tuple)
        # Double-checked locking pattern to initialize an on-demand concurrency tracker if it does not exist
        if not on_demand_tracker:
            with self.on_demand_init_lock:
                on_demand_tracker = self.on_demand_concurrency_trackers.get(scope_tuple)
                if not on_demand_tracker:
                    on_demand_tracker = self.on_demand_concurrency_trackers[scope_tuple] = (
                        ConcurrencyTracker()
                    )

        provisioned_tracker = self.provisioned_concurrency_trackers.get(scope_tuple)
        # Double-checked locking pattern to initialize a provisioned concurrency tracker if it does not exist
        if not provisioned_tracker:
            with self.provisioned_concurrency_init_lock:
                provisioned_tracker = self.provisioned_concurrency_trackers.get(scope_tuple)
                if not provisioned_tracker:
                    provisioned_tracker = self.provisioned_concurrency_trackers[scope_tuple] = (
                        ConcurrencyTracker()
                    )

        unqualified_function_arn = function_version.id.unqualified_arn()
        qualified_arn = function_version.id.qualified_arn()

        lease_type = None
        # HACK: skip reserved and provisioned concurrency if function not available (e.g., in Lambda@Edge)
        if function is not None:
            with provisioned_tracker.lock:
                # 1) Check for free provisioned concurrency
                provisioned_concurrency_config = function.provisioned_concurrency_configs.get(
                    function_version.id.qualifier
                )
                if not provisioned_concurrency_config:
                    # check if any aliases point to the current version, and check the provisioned concurrency config
                    # for them. There can be only one config for a version, not matter if defined on the alias or version itself.
                    for alias in function.aliases.values():
                        if alias.function_version == function_version.id.qualifier:
                            provisioned_concurrency_config = (
                                function.provisioned_concurrency_configs.get(alias.name)
                            )
                            break
                # Favor provisioned concurrency if configured and ready
                # TODO: test updating provisioned concurrency? Does AWS serve on-demand during updates?
                # Potential challenge if an update happens in between reserving the lease here and actually assigning
                # * Increase provisioned: It could happen that we give a lease for provisioned-concurrency although
                # brand new provisioned environments are not yet initialized.
                # * Decrease provisioned: It could happen that we have running invocations that should still be counted
                # against the limit but they are not because we already updated the concurrency config to fewer envs.
                if (
                    provisioned_concurrency_config
                    and provisioned_state.status == ProvisionedConcurrencyStatusEnum.READY
                ):
                    available_provisioned_concurrency = (
                        provisioned_concurrency_config.provisioned_concurrent_executions
                        - provisioned_tracker.concurrent_executions[qualified_arn]
                    )
                    if available_provisioned_concurrency > 0:
                        provisioned_tracker.increment(qualified_arn)
                        lease_type = InitializationType.provisioned_concurrency

        if not lease_type:
            with on_demand_tracker.lock:
                # 2) If reserved concurrency is set AND no provisioned concurrency available:
                # => Check if enough reserved concurrency is available for the specific function.
                # HACK: skip reserved if function not available (e.g., in Lambda@Edge)
                if function and function.reserved_concurrent_executions is not None:
                    on_demand_running_invocation_count = on_demand_tracker.concurrent_executions[
                        unqualified_function_arn
                    ]
                    available_reserved_concurrency = (
                        function.reserved_concurrent_executions
                        - calculate_provisioned_concurrency_sum(function)
                        - on_demand_running_invocation_count
                    )
                    if available_reserved_concurrency > 0:
                        on_demand_tracker.increment(unqualified_function_arn)
                        lease_type = InitializationType.on_demand
                    else:
                        extras = {
                            "available_reserved_concurrency": available_reserved_concurrency,
                            "reserved_concurrent_executions": function.reserved_concurrent_executions,
                            "provisioned_concurrency_sum": calculate_provisioned_concurrency_sum(
                                function
                            ),
                            "on_demand_running_invocation_count": on_demand_running_invocation_count,
                        }
                        LOG.debug("Insufficient reserved concurrency available: %s", extras)
                        raise TooManyRequestsException(
                            "Rate Exceeded.",
                            Reason="ReservedFunctionConcurrentInvocationLimitExceeded",
                            Type="User",
                        )
                # 3) If no reserved concurrency is set AND no provisioned concurrency available.
                # => Check the entire state within the scope of account and region.
                else:
                    # TODO: Consider a dedicated counter for unavailable concurrency with locks for updates on
                    #  reserved and provisioned concurrency if this is too slow
                    # The total concurrency allocated or used (i.e., unavailable concurrency) per account and region
                    total_used_concurrency = 0
                    store = lambda_stores[account][region]
                    for fn in store.functions.values():
                        if fn.reserved_concurrent_executions is not None:
                            total_used_concurrency += fn.reserved_concurrent_executions
                        else:
                            fn_provisioned_concurrency = calculate_provisioned_concurrency_sum(fn)
                            total_used_concurrency += fn_provisioned_concurrency
                            fn_on_demand_concurrent_executions = (
                                on_demand_tracker.concurrent_executions[
                                    fn.latest().id.unqualified_arn()
                                ]
                            )
                            total_used_concurrency += fn_on_demand_concurrent_executions

                    available_unreserved_concurrency = (
                        config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS - total_used_concurrency
                    )
                    if available_unreserved_concurrency > 0:
                        on_demand_tracker.increment(unqualified_function_arn)
                        lease_type = InitializationType.on_demand
                    else:
                        if available_unreserved_concurrency < 0:
                            LOG.error(
                                "Invalid function concurrency state detected for function: %s | available unreserved concurrency: %d",
                                unqualified_function_arn,
                                available_unreserved_concurrency,
                            )
                        extras = {
                            "available_unreserved_concurrency": available_unreserved_concurrency,
                            "lambda_limits_concurrent_executions": config.LAMBDA_LIMITS_CONCURRENT_EXECUTIONS,
                            "total_used_concurrency": total_used_concurrency,
                        }
                        LOG.debug("Insufficient unreserved concurrency available: %s", extras)
                        raise TooManyRequestsException(
                            "Rate Exceeded.",
                            Reason="ReservedFunctionConcurrentInvocationLimitExceeded",
                            Type="User",
                        )
        try:
            yield lease_type
        finally:
            if lease_type == InitializationType.provisioned_concurrency:
                provisioned_tracker.atomic_decrement(qualified_arn)
            elif lease_type == InitializationType.on_demand:
                on_demand_tracker.atomic_decrement(unqualified_function_arn)
            else:
                LOG.error(
                    "Invalid lease type detected for function: %s: %s",
                    unqualified_function_arn,
                    lease_type,
                )
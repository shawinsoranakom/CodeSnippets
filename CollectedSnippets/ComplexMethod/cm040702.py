def on_after_state_load(self):
        self.lambda_service = LambdaService()
        self.router.lambda_service = self.lambda_service

        for account_id, account_bundle in lambda_stores.items():
            for region_name, state in account_bundle.items():
                for fn in state.functions.values():
                    # HACK to model a volatile variable that should be ignored for persistence
                    # Identifier unique to this function and LocalStack instance.
                    # A LocalStack restart or persistence load should create a new instance id.
                    # Used for retaining invoke queues across version updates for $LATEST, but
                    # separate unrelated instances.
                    fn.instance_id = short_uid()

                    for fn_version in fn.versions.values():
                        try:
                            # Skip function versions that were being deleted
                            if fn_version.config.state.state == State.Deleting:
                                continue

                            # Skip function versions whose capacity provider has been stopped
                            if fn_version.config.capacity_provider_config:
                                cp_arn = fn_version.config.capacity_provider_config[
                                    "LambdaManagedInstancesCapacityProviderConfig"
                                ]["CapacityProviderArn"]
                                cp_name = cp_arn.split(":")[-1]
                                cp = state.capacity_providers.get(cp_name)
                                if cp and cp.DesiredState == DesiredCapacityProviderState.Stopped:
                                    continue

                            # $LATEST is not invokable for Lambda functions with a capacity provider
                            # and has a different State (i.e., ActiveNonInvokable)
                            is_capacity_provider_latest = (
                                fn_version.config.capacity_provider_config
                                and fn_version.id.qualifier == "$LATEST"
                            )
                            if not is_capacity_provider_latest:
                                # Restore the "Pending" state for the function version and start it
                                new_state = VersionState(
                                    state=State.Pending,
                                    code=StateReasonCode.Creating,
                                    reason="The function is being created.",
                                )
                                new_config = dataclasses.replace(fn_version.config, state=new_state)
                                new_version = dataclasses.replace(fn_version, config=new_config)
                                fn.versions[fn_version.id.qualifier] = new_version
                                self.lambda_service.create_function_version(fn_version).result(
                                    timeout=5
                                )
                        except Exception:
                            LOG.warning(
                                "Failed to restore function version %s",
                                fn_version.id.qualified_arn(),
                                exc_info=LOG.isEnabledFor(logging.DEBUG),
                            )
                    # restore provisioned concurrency per function considering both versions and aliases
                    for (
                        provisioned_qualifier,
                        provisioned_config,
                    ) in fn.provisioned_concurrency_configs.items():
                        fn_arn = None
                        try:
                            if api_utils.qualifier_is_alias(provisioned_qualifier):
                                alias = fn.aliases.get(provisioned_qualifier)
                                resolved_version = fn.versions.get(alias.function_version)
                                fn_arn = resolved_version.id.qualified_arn()
                            elif api_utils.qualifier_is_version(provisioned_qualifier):
                                fn_version = fn.versions.get(provisioned_qualifier)
                                fn_arn = fn_version.id.qualified_arn()
                            else:
                                raise InvalidParameterValueException(
                                    "Invalid qualifier type:"
                                    " Qualifier can only be an alias or a version for provisioned concurrency."
                                )

                            manager = self.lambda_service.get_lambda_version_manager(fn_arn)
                            manager.update_provisioned_concurrency_config(
                                provisioned_config.provisioned_concurrent_executions
                            )
                        except Exception:
                            LOG.warning(
                                "Failed to restore provisioned concurrency %s for function %s",
                                provisioned_config,
                                fn_arn,
                                exc_info=LOG.isEnabledFor(logging.DEBUG),
                            )

                for esm in state.event_source_mappings.values():
                    # Restores event source workers
                    function_arn = esm.get("FunctionArn")

                    # TODO: How do we know the event source is up?
                    # A basic poll to see if the mapped Lambda function is active/failed
                    if not poll_condition(
                        lambda: (
                            get_function_version_from_arn(function_arn).config.state.state
                            in [State.Active, State.Failed]
                        ),
                        timeout=10,
                    ):
                        LOG.warning(
                            "Creating ESM for Lambda that is not in running state: %s",
                            function_arn,
                        )

                    function_version = get_function_version_from_arn(function_arn)
                    function_role = function_version.config.role

                    is_esm_enabled = esm.get("State", EsmState.DISABLED) not in (
                        EsmState.DISABLED,
                        EsmState.DISABLING,
                    )
                    esm_worker = EsmWorkerFactory(
                        esm, function_role, is_esm_enabled
                    ).get_esm_worker()

                    # Note: a worker is created in the DISABLED state if not enabled
                    esm_worker.create()
                    # TODO: assigning the esm_worker to the dict only works after .create(). Could it cause a race
                    #  condition if we get a shutdown here and have a worker thread spawned but not accounted for?
                    self.esm_workers[esm_worker.uuid] = esm_worker
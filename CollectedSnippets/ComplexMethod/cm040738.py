def update_version_state(
        self, function_version: FunctionVersion, new_state: VersionState
    ) -> None:
        """
        Update the version state for the given function version.

        This will perform a rollover to the given function if the new state is active and there is a previously
        running version registered. The old version will be shutdown and its code deleted.

        If the new state is failed, it will abort the update and mark it as failed.
        If an older version is still running, it will keep running.

        :param function_version: Version reporting the state
        :param new_state: New state
        """
        function_arn = function_version.qualified_arn
        try:
            old_version = None
            old_event_manager = None
            with self.lambda_version_manager_lock:
                new_version_manager = self.lambda_starting_versions.pop(function_arn)
                if not new_version_manager:
                    raise ValueError(
                        f"Version {function_arn} reporting state {new_state.state} does exist in the starting versions."
                    )
                if new_state.state == State.Active:
                    old_version = self.lambda_running_versions.get(function_arn, None)
                    old_event_manager = self.event_managers.get(function_arn, None)
                    self.lambda_running_versions[function_arn] = new_version_manager
                    self.event_managers[function_arn] = LambdaEventManager(
                        version_manager=new_version_manager
                    )
                    self.event_managers[function_arn].start()
                    update_status = UpdateStatus(status=LastUpdateStatus.Successful)
                elif new_state.state == State.Failed:
                    update_status = UpdateStatus(status=LastUpdateStatus.Failed)
                    self.task_executor.submit(new_version_manager.stop)
                elif (
                    new_state.state == State.ActiveNonInvocable
                    and function_version.config.capacity_provider_config
                ):
                    update_status = UpdateStatus(status=LastUpdateStatus.Successful)
                else:
                    # TODO what to do if state pending or inactive is supported?
                    self.task_executor.submit(new_version_manager.stop)
                    LOG.error(
                        "State %s for version %s should not have been reported. New version will be stopped.",
                        new_state,
                        function_arn,
                    )
                    return

            # TODO is it necessary to get the version again? Should be locked for modification anyway
            # Without updating the new state, the function would not change to active, last_update would be missing, and
            # the revision id would not be updated.
            state = lambda_stores[function_version.id.account][function_version.id.region]
            # FIXME this will fail if the function is deleted during this code lines here
            function = state.functions.get(function_version.id.function_name)
            if old_event_manager:
                self.task_executor.submit(old_event_manager.stop_for_update)
            if old_version:
                # if there is an old version, we assume it is an update, and stop the old one
                self.task_executor.submit(old_version.stop)
                if function:
                    self.task_executor.submit(
                        destroy_code_if_not_used, old_version.function_version.config.code, function
                    )
            if not function:
                LOG.debug("Function %s was deleted during status update", function_arn)
                return
            current_version = function.versions[function_version.id.qualifier]
            new_version_manager.state = new_state
            new_version_state = dataclasses.replace(
                current_version,
                config=dataclasses.replace(
                    current_version.config, state=new_state, last_update=update_status
                ),
            )
            state.functions[function_version.id.function_name].versions[
                function_version.id.qualifier
            ] = new_version_state

        except Exception:
            LOG.error(
                "Failed to update function version for arn %s",
                function_arn,
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )
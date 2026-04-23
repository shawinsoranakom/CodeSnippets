def _eval_integration_pattern(
        self,
        env: Environment,
        resource_runtime_part: ResourceRuntimePart,
        normalised_parameters: dict,
        state_credentials: StateCredentials,
    ) -> None:
        task_output = env.stack.pop()

        # Initialise the waitForTaskToken Callback endpoint for this task if supported.
        callback_endpoint: CallbackEndpoint | None = None
        if ResourceCondition.WaitForTaskToken in self._supported_integration_patterns:
            callback_id = env.states.context_object.context_object_data["Task"]["Token"]
            callback_endpoint = env.callback_pool_manager.get(callback_id)

        # Setup resources for timeout control.
        self.timeout.eval(env=env)
        timeout_seconds = env.stack.pop()

        # Setup resources for heartbeat workloads if necessary.
        heartbeat_endpoint: HeartbeatEndpoint | None = None
        if self.heartbeat:
            self.heartbeat.eval(env=env)
            heartbeat_seconds = env.stack.pop()
            heartbeat_endpoint: HeartbeatEndpoint = callback_endpoint.setup_heartbeat_endpoint(
                heartbeat_seconds=heartbeat_seconds
            )

        # Collect the output of the integration pattern.
        outcome: CallbackOutcome | Any
        try:
            if self.resource.condition == ResourceCondition.WaitForTaskToken:
                outcome = self._eval_wait_for_task_token(
                    env=env,
                    timeout_seconds=timeout_seconds,
                    callback_endpoint=callback_endpoint,
                    heartbeat_endpoint=heartbeat_endpoint,
                )
            else:
                # Sync operations require the task output as input.
                env.stack.append(task_output)
                if self.resource.condition == ResourceCondition.Sync:
                    sync_resolver = self._build_sync_resolver(
                        env=env,
                        resource_runtime_part=resource_runtime_part,
                        normalised_parameters=normalised_parameters,
                        state_credentials=state_credentials,
                    )
                else:
                    # The condition checks about the resource's condition is exhaustive leaving
                    # only Sync2 ResourceCondition types in this block.
                    sync_resolver = self._build_sync2_resolver(
                        env=env,
                        resource_runtime_part=resource_runtime_part,
                        normalised_parameters=normalised_parameters,
                        state_credentials=state_credentials,
                    )

                outcome = self._eval_sync(
                    env=env,
                    timeout_seconds=timeout_seconds,
                    callback_endpoint=callback_endpoint,
                    heartbeat_endpoint=heartbeat_endpoint,
                    sync_resolver=sync_resolver,
                )
        except Exception as integration_exception:
            outcome = integration_exception
        finally:
            # Now that the outcome is collected or the exception is about to be passed upstream, and the process has
            # finished, ensure all waiting # threads on this endpoint (or task) will stop. This is in an effort to
            # release resources sooner than when these would eventually synchronise with the updated environment
            # state of this task.
            if callback_endpoint:
                callback_endpoint.interrupt_all()

        # Handle Callback outcome types.
        if isinstance(outcome, CallbackOutcomeTimedOut):
            raise CallbackTimeoutError()
        elif isinstance(outcome, HeartbeatTimedOut):
            raise HeartbeatTimeoutError()
        elif isinstance(outcome, CallbackOutcomeFailure):
            raise CallbackOutcomeFailureError(callback_outcome_failure=outcome)
        elif isinstance(outcome, CallbackOutcomeSuccess):
            outcome_output = json.loads(outcome.output)
            env.stack.append(outcome_output)
        # Pass evaluation exception upstream for error handling.
        elif isinstance(outcome, Exception):
            raise outcome
        # Otherwise the outcome is the result of the integration pattern (sync, sync2)
        # therefore push it onto the evaluation stack for the next operations.
        else:
            env.stack.append(outcome)
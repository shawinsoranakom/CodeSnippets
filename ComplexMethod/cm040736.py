def invoke(self, *, invocation: Invocation) -> InvocationResult:
        """
        synchronous invoke entrypoint

        0. check counter, get lease
        1. try to get an inactive (no active invoke) environment
        2.(allgood) send invoke to environment
        3. wait for invocation result
        4. return invocation result & release lease

        2.(nogood) fail fast fail hard

        """
        LOG.debug(
            "Got an invocation for function %s with request_id %s",
            self.function_arn,
            invocation.request_id,
        )
        if self.shutdown_event.is_set():
            message = f"Got an invocation with request_id {invocation.request_id} for a version shutting down"
            LOG.warning(message)
            raise ServiceException(message)

        # If the environment has debugging enabled, route the invocation there;
        # debug environments bypass Lambda service quotas.
        if self.ldm_provisioner and (
            ldm_execution_environment := self.ldm_provisioner.get_execution_environment(
                qualified_lambda_arn=self.function_version.qualified_arn,
                user_agent=invocation.user_agent,
            )
        ):
            try:
                invocation_result = ldm_execution_environment.invoke(invocation)
                invocation_result.executed_version = self.function_version.id.qualifier
                self.store_logs(
                    invocation_result=invocation_result, execution_env=ldm_execution_environment
                )
            except CancelledError as e:
                # Timeouts for invocation futures are managed by LDM, a cancelled error here is
                # aligned with the debug container terminating whilst debugging/invocation.
                LOG.debug("LDM invocation future encountered a cancelled error: '%s'", e)
                invocation_result = InvocationResult(
                    request_id="",
                    payload=to_bytes(
                        "The invocation was canceled because the debug configuration "
                        "was removed or the operation timed out"
                    ),
                    is_error=True,
                    logs="",
                    executed_version=self.function_version.id.qualifier,
                )
            except StatusErrorException as e:
                invocation_result = InvocationResult(
                    request_id="",
                    payload=e.payload,
                    is_error=True,
                    logs="",
                    executed_version=self.function_version.id.qualifier,
                )
            finally:
                ldm_execution_environment.release()
            return invocation_result

        with self.counting_service.get_invocation_lease(
            self.function, self.function_version, self.provisioned_state
        ) as provisioning_type:
            # TODO: potential race condition when changing provisioned concurrency after getting the lease but before
            #   getting an environment
            try:
                # Blocks and potentially creates a new execution environment for this invocation
                with self.assignment_service.get_environment(
                    self.id, self.function_version, provisioning_type
                ) as execution_env:
                    invocation_result = execution_env.invoke(invocation)
                    invocation_result.executed_version = self.function_version.id.qualifier
                    self.store_logs(
                        invocation_result=invocation_result, execution_env=execution_env
                    )
            except StatusErrorException as e:
                invocation_result = InvocationResult(
                    request_id="",
                    payload=e.payload,
                    is_error=True,
                    logs="",
                    executed_version=self.function_version.id.qualifier,
                )

        function_id = self.function_version.id
        # Record CloudWatch metrics in separate threads
        # MAYBE reuse threads rather than starting new threads upon every invocation
        if invocation_result.is_error:
            start_thread(
                lambda *args, **kwargs: record_cw_metric_error(
                    function_name=function_id.function_name,
                    account_id=function_id.account,
                    region_name=function_id.region,
                ),
                name=f"record-cloudwatch-metric-error-{function_id.function_name}:{function_id.qualifier}",
            )
        else:
            start_thread(
                lambda *args, **kwargs: record_cw_metric_invocation(
                    function_name=function_id.function_name,
                    account_id=function_id.account,
                    region_name=function_id.region,
                ),
                name=f"record-cloudwatch-metric-{function_id.function_name}:{function_id.qualifier}",
            )
        # TODO: consider using the same prefix logging as in error case for execution environment.
        #   possibly as separate named logger.
        if invocation_result.logs is not None:
            LOG.debug("Got logs for invocation '%s'", invocation.request_id)
            for log_line in invocation_result.logs.splitlines():
                LOG.debug(
                    "[%s-%s] %s",
                    function_id.function_name,
                    invocation.request_id,
                    truncate(log_line, config.LAMBDA_TRUNCATE_STDOUT),
                )
        else:
            LOG.warning(
                "[%s] Error while printing logs for function '%s': Received no logs from environment.",
                invocation.request_id,
                function_id.function_name,
            )
        return invocation_result
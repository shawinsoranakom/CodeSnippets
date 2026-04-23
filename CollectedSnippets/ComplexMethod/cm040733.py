def handle_message(self, message: dict) -> None:
        failure_cause = None
        qualifier = self.version_manager.function_version.id.qualifier
        function_config = self.version_manager.function_version.config
        event_invoke_config = self.version_manager.function.event_invoke_configs.get(qualifier)
        runtime = None
        status = None
        # TODO: handle initialization_type provisioned-concurrency, which requires enriching invocation_result
        initialization_type = (
            FunctionInitializationType.lambda_managed_instances
            if function_config.capacity_provider_config
            else FunctionInitializationType.on_demand
        )
        try:
            sqs_invocation = SQSInvocation.decode(message["Body"])
            invocation = sqs_invocation.invocation
            try:
                invocation_result = self.version_manager.invoke(invocation=invocation)
                status = FunctionStatus.success
            except Exception as e:
                # Reserved concurrency == 0
                if self.version_manager.function.reserved_concurrent_executions == 0:
                    failure_cause = "ZeroReservedConcurrency"
                    status = FunctionStatus.zero_reserved_concurrency_error
                # Maximum event age expired (lookahead for next retry)
                elif not has_enough_time_for_retry(sqs_invocation, event_invoke_config):
                    failure_cause = "EventAgeExceeded"
                    status = FunctionStatus.event_age_exceeded_error

                if failure_cause:
                    invocation_result = InvocationResult(
                        is_error=True, request_id=invocation.request_id, payload=None, logs=None
                    )
                    self.process_failure_destination(
                        sqs_invocation, invocation_result, event_invoke_config, failure_cause
                    )
                    self.process_dead_letter_queue(sqs_invocation, invocation_result)
                    return
                # 3) Otherwise, retry without increasing counter
                status = self.process_throttles_and_system_errors(sqs_invocation, e)
                return
            finally:
                sqs_client = get_sqs_client(self.version_manager.function_version)
                sqs_client.delete_message(
                    QueueUrl=self.event_queue_url, ReceiptHandle=message["ReceiptHandle"]
                )
                assert status, "status MUST be set before returning"
                function_counter.labels(
                    operation=FunctionOperation.invoke,
                    runtime=runtime or "n/a",
                    status=status,
                    invocation_type=InvocationType.Event,
                    package_type=function_config.package_type,
                    initialization_type=initialization_type,
                ).increment()

            # Good summary blogpost: https://haithai91.medium.com/aws-lambdas-retry-behaviors-edff90e1cf1b
            # Asynchronous invocation handling: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async.html
            # https://aws.amazon.com/blogs/compute/introducing-new-asynchronous-invocation-metrics-for-aws-lambda/
            max_retry_attempts = 2
            if event_invoke_config and event_invoke_config.maximum_retry_attempts is not None:
                max_retry_attempts = event_invoke_config.maximum_retry_attempts

            assert invocation_result, "Invocation result MUST exist if we are not returning before"

            # An invocation error either leads to a terminal failure or to a scheduled retry
            if invocation_result.is_error:  # invocation error
                failure_cause = None
                # Reserved concurrency == 0
                if self.version_manager.function.reserved_concurrent_executions == 0:
                    failure_cause = "ZeroReservedConcurrency"
                # Maximum retries exhausted
                elif sqs_invocation.retries >= max_retry_attempts:
                    failure_cause = "RetriesExhausted"
                # TODO: test what happens if max event age expired before it gets scheduled the first time?!
                # Maximum event age expired (lookahead for next retry)
                elif not has_enough_time_for_retry(sqs_invocation, event_invoke_config):
                    failure_cause = "EventAgeExceeded"

                if failure_cause:  # handle failure destination and DLQ
                    self.process_failure_destination(
                        sqs_invocation, invocation_result, event_invoke_config, failure_cause
                    )
                    self.process_dead_letter_queue(sqs_invocation, invocation_result)
                    return
                else:  # schedule retry
                    sqs_invocation.retries += 1
                    # Assumption: We assume that the internal exception retries counter is reset after
                    #  an invocation that does not throw an exception
                    sqs_invocation.exception_retries = 0
                    # LAMBDA_RETRY_BASE_DELAY_SECONDS has a limit of 300s because the maximum SQS DelaySeconds
                    # is 15 minutes (900s) and the maximum retry count is 3. SQS quota for "Message timer":
                    # https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html
                    delay_seconds = sqs_invocation.retries * config.LAMBDA_RETRY_BASE_DELAY_SECONDS
                    # TODO: max SQS message size limit could break parity with AWS because
                    #  our SQSInvocation contains additional fields! 256kb is max for both Lambda payload + SQS
                    # TODO: write test with max SQS message size
                    sqs_client.send_message(
                        QueueUrl=self.event_queue_url,
                        MessageBody=sqs_invocation.encode(),
                        DelaySeconds=delay_seconds,
                    )
                    return
            else:  # invocation success
                self.process_success_destination(
                    sqs_invocation, invocation_result, event_invoke_config
                )
        except Exception as e:
            LOG.error(
                "Error handling lambda invoke %s", e, exc_info=LOG.isEnabledFor(logging.DEBUG)
            )
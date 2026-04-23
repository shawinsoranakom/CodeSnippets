def invoke(
        self,
        context: RequestContext,
        function_name: NamespacedFunctionName,
        invocation_type: InvocationType | None = None,
        log_type: LogType | None = None,
        client_context: String | None = None,
        durable_execution_name: DurableExecutionName | None = None,
        payload: IO[Blob] | None = None,
        qualifier: NumericLatestPublishedOrAliasQualifier | None = None,
        tenant_id: TenantId | None = None,
        **kwargs,
    ) -> InvocationResponse:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )

        user_agent = context.request.user_agent.string

        time_before = time.perf_counter()
        try:
            invocation_result = self.lambda_service.invoke(
                function_name=function_name,
                qualifier=qualifier,
                region=region,
                account_id=account_id,
                invocation_type=invocation_type,
                client_context=client_context,
                request_id=context.request_id,
                trace_context=context.trace_context,
                payload=payload.read() if payload else None,
                user_agent=user_agent,
            )
        except ServiceException:
            raise
        except EnvironmentStartupTimeoutException as e:
            raise LambdaServiceException(
                f"[{context.request_id}] Timeout while starting up lambda environment for function {function_name}:{qualifier}"
            ) from e
        except Exception as e:
            LOG.error(
                "[%s] Error while invoking lambda %s",
                context.request_id,
                function_name,
                exc_info=LOG.isEnabledFor(logging.DEBUG),
            )
            raise LambdaServiceException(
                f"[{context.request_id}] Internal error while executing lambda {function_name}:{qualifier}. Caused by {type(e).__name__}: {e}"
            ) from e

        if invocation_type == InvocationType.Event:
            # This happens when invocation type is event
            return InvocationResponse(StatusCode=202)
        if invocation_type == InvocationType.DryRun:
            # This happens when invocation type is dryrun
            return InvocationResponse(StatusCode=204)
        LOG.debug("Lambda invocation duration: %0.2fms", (time.perf_counter() - time_before) * 1000)

        response = InvocationResponse(
            StatusCode=200,
            Payload=invocation_result.payload,
            ExecutedVersion=invocation_result.executed_version,
        )

        if invocation_result.is_error:
            response["FunctionError"] = "Unhandled"

        if log_type == LogType.Tail:
            response["LogResult"] = to_str(
                base64.b64encode(to_bytes(invocation_result.logs)[-4096:])
            )

        return response
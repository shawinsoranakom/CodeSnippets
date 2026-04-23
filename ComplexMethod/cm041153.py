def invoke(self, invocation_context: ApiInvocationContext):
        uri = (
            invocation_context.integration.get("uri")
            or invocation_context.integration.get("integrationUri")
            or ""
        )
        action = uri.split("/")[-1]

        if invocation_context.integration.get("IntegrationType") == "AWS_PROXY":
            payload = self._create_request_parameters(invocation_context)
        elif APPLICATION_JSON in invocation_context.integration.get("requestTemplates", {}):
            payload = self.request_templates.render(invocation_context)
            payload = json.loads(payload)
        else:
            payload = json.loads(invocation_context.data)

        client = get_service_factory(
            region_name=invocation_context.region_name,
            role_arn=invocation_context.integration.get("credentials"),
        ).stepfunctions

        if isinstance(payload.get("input"), dict):
            payload["input"] = json.dumps(payload["input"])

        # Hot fix since step functions local package responses: Unsupported Operation: 'StartSyncExecution'
        method_name = (
            camel_to_snake_case(action) if action != "StartSyncExecution" else "start_execution"
        )

        try:
            # call method on step function client
            method = getattr(client, method_name)
        except AttributeError:
            msg = f"Invalid step function action: {method_name}"
            LOG.error(msg)
            return StepFunctionIntegration._create_response(
                HTTPStatus.BAD_REQUEST.value,
                headers={"Content-Type": APPLICATION_JSON},
                data=json.dumps({"message": msg}),
            )

        result = method(**payload)
        result = json_safe(remove_attributes(result, ["ResponseMetadata"]))
        response = StepFunctionIntegration._create_response(
            HTTPStatus.OK.value,
            mock_aws_request_headers(
                "stepfunctions",
                aws_access_key_id=invocation_context.account_id,
                region_name=invocation_context.region_name,
            ),
            data=json.dumps(result),
        )
        if action == "StartSyncExecution":
            # poll for the execution result and return it
            result = await_sfn_execution_result(result["executionArn"])
            result_status = result.get("status")
            if result_status != "SUCCEEDED":
                return StepFunctionIntegration._create_response(
                    HTTPStatus.INTERNAL_SERVER_ERROR.value,
                    headers={"Content-Type": APPLICATION_JSON},
                    data=json.dumps(
                        {
                            "message": "StepFunctions execution {} failed with status '{}'".format(
                                result["executionArn"], result_status
                            )
                        }
                    ),
                )

            result = json_safe(result)
            response = requests_response(content=result)

        # apply response templates
        invocation_context.response = response
        response._content = self.response_templates.render(invocation_context)
        return response
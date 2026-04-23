def invoke(self, invocation_context: ApiInvocationContext):
        self.validate_integration_method(invocation_context)
        uri = (
            invocation_context.integration.get("uri")
            or invocation_context.integration.get("integrationUri")
            or ""
        )
        invocation_context.context = get_event_request_context(invocation_context)
        relative_path, query_string_params = extract_query_string_params(
            path=invocation_context.path_with_query_string
        )
        try:
            path_params = extract_path_params(
                path=relative_path, extracted_path=invocation_context.resource_path
            )
            invocation_context.path_params = path_params
        except Exception:
            pass

        func_arn = uri
        if ":lambda:path" in uri:
            func_arn = uri.split(":lambda:path")[1].split("functions/")[1].split("/invocations")[0]

        if invocation_context.authorizer_type:
            invocation_context.context["authorizer"] = invocation_context.authorizer_result

        payload = self.request_templates.render(invocation_context)

        result = self.process_apigateway_invocation(
            func_arn=func_arn,
            path=relative_path,
            payload=payload,
            invocation_context=invocation_context,
            query_string_params=query_string_params,
        )

        response = LambdaResponse()
        response.headers.update({"content-type": "application/json"})
        parsed_result = json.loads(str(result or "{}"))
        parsed_result = common.json_safe(parsed_result)
        parsed_result = {} if parsed_result is None else parsed_result

        if set(parsed_result) - {
            "body",
            "statusCode",
            "headers",
            "isBase64Encoded",
            "multiValueHeaders",
        }:
            LOG.warning(
                'Lambda output should follow the next JSON format: { "isBase64Encoded": true|false, "statusCode": httpStatusCode, "headers": { "headerName": "headerValue", ... },"body": "..."}\n Lambda output: %s',
                parsed_result,
            )
            response.status_code = 502
            response._content = json.dumps({"message": "Internal server error"})
            return response

        response.status_code = int(parsed_result.get("statusCode", 200))
        parsed_headers = parsed_result.get("headers", {})
        if parsed_headers is not None:
            response.headers.update(parsed_headers)
        try:
            result_body = parsed_result.get("body")
            if isinstance(result_body, dict):
                response._content = json.dumps(result_body)
            else:
                body_bytes = to_bytes(result_body or "")
                if parsed_result.get("isBase64Encoded", False):
                    body_bytes = base64.b64decode(body_bytes)
                response._content = body_bytes
        except Exception as e:
            LOG.warning("Couldn't set Lambda response content: %s", e)
            response._content = "{}"
        response.multi_value_headers = parsed_result.get("multiValueHeaders") or {}

        # apply custom response template
        self.update_content_length(response)
        invocation_context.response = response

        return invocation_context.response
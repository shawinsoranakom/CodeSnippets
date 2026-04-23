def invoke(self, context: RestApiInvocationContext) -> EndpointResponse:
        integration_req: IntegrationRequest = context.integration_request
        method = integration_req["http_method"]

        if method != HTTPMethod.POST:
            LOG.warning(
                "The 'AWS_PROXY' integration can only be used with the POST integration method.",
            )
            raise IntegrationFailureError("Internal server error")

        input_event = self.create_lambda_input_event(context)

        # TODO: verify stage variables rendering in AWS_PROXY
        integration_uri = integration_req["uri"]

        function_arn = get_lambda_function_arn_from_invocation_uri(integration_uri)
        source_arn = get_source_arn(context)

        # TODO: write test for credentials rendering
        if credentials := context.integration.get("credentials"):
            credentials = render_uri_with_stage_variables(credentials, context.stage_variables)

        try:
            lambda_payload = self.call_lambda(
                function_arn=function_arn,
                event=to_bytes(json.dumps(input_event)),
                source_arn=source_arn,
                credentials=credentials,
            )

        except ClientError as e:
            LOG.warning(
                "Exception during integration invocation: '%s'",
                e,
            )
            status_code = 502
            if e.response["Error"]["Code"] == "AccessDeniedException":
                status_code = 500
            raise IntegrationFailureError("Internal server error", status_code=status_code) from e

        except Exception as e:
            LOG.warning(
                "Unexpected exception during integration invocation: '%s'",
                e,
            )
            raise IntegrationFailureError("Internal server error", status_code=502) from e

        lambda_response = self.parse_lambda_response(lambda_payload)

        headers = Headers({"Content-Type": APPLICATION_JSON})

        response_headers = self._merge_lambda_response_headers(lambda_response)
        headers.update(response_headers)

        # TODO: maybe centralize this flag inside the context, when we are also using it for other integration types
        #  AWS_PROXY behaves a bit differently, but this could checked only once earlier
        binary_response_accepted = mime_type_matches_binary_media_types(
            mime_type=context.invocation_request["headers"].get("Accept"),
            binary_media_types=context.deployment.rest_api.rest_api.get("binaryMediaTypes", []),
        )
        body = self._parse_body(
            body=lambda_response.get("body"),
            is_base64_encoded=binary_response_accepted and lambda_response.get("isBase64Encoded"),
        )

        return EndpointResponse(
            headers=headers,
            body=body,
            status_code=int(lambda_response.get("statusCode") or 200),
        )
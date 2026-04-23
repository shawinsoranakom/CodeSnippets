def convert_body(
        context: RestApiInvocationContext,
        body: bytes,
        content_handling: ContentHandlingStrategy | None,
    ) -> bytes | str:
        """
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings.html
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-payload-encodings-workflow.html
        :param context: RestApiInvocationContext
        :param body: the endpoint response body
        :param content_handling: the contentHandling of the IntegrationResponse
        :return: the body, either as is, or converted depending on the table in the second link
        """

        request: InvocationRequest = context.invocation_request
        response: EndpointResponse = context.endpoint_response
        binary_media_types = context.deployment.rest_api.rest_api.get("binaryMediaTypes", [])

        is_binary_payload = mime_type_matches_binary_media_types(
            mime_type=response["headers"].get("Content-Type"),
            binary_media_types=binary_media_types,
        )
        is_binary_accept = mime_type_matches_binary_media_types(
            mime_type=request["headers"].get("Accept"),
            binary_media_types=binary_media_types,
        )

        if is_binary_payload:
            if (
                content_handling and content_handling == ContentHandlingStrategy.CONVERT_TO_TEXT
            ) or (not content_handling and not is_binary_accept):
                body = base64.b64encode(body)
        else:
            # this means the Payload is of type `Text` in AWS terms for the table
            if (
                content_handling and content_handling == ContentHandlingStrategy.CONVERT_TO_TEXT
            ) or (not content_handling and not is_binary_accept):
                body = body.decode(encoding="UTF-8", errors="replace")
            else:
                try:
                    body = base64.b64decode(body)
                except ValueError:
                    raise InternalServerError("Internal server error")

        return body
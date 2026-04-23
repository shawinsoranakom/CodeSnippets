def select_integration_response(matched_part: str, invocation_context: ApiInvocationContext):
    int_responses = invocation_context.integration.get("integrationResponses") or {}
    if select_by_pattern := [
        response
        for response in int_responses.values()
        if response.get("selectionPattern")
        and re.match(response.get("selectionPattern"), matched_part)
    ]:
        selected_response = select_by_pattern[0]
        if len(select_by_pattern) > 1:
            LOG.warning(
                "Multiple integration responses matching '%s' statuscode. Choosing '%s' (first).",
                matched_part,
                selected_response["statusCode"],
            )
    else:
        # choose default return code
        default_responses = [
            response for response in int_responses.values() if not response.get("selectionPattern")
        ]
        if not default_responses:
            raise ApiGatewayIntegrationError("Internal server error", 500)

        selected_response = default_responses[0]
        if len(default_responses) > 1:
            LOG.warning(
                "Multiple default integration responses. Choosing %s (first).",
                selected_response["statusCode"],
            )
    return selected_response
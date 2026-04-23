def select_integration_response(
        selection_value: str, integration_responses: dict[str, IntegrationResponse]
    ) -> IntegrationResponse:
        if not integration_responses:
            LOG.warning(
                "Configuration error: No match for output mapping and no default output mapping configured. "
                "Endpoint Response Status Code: %s",
                selection_value,
            )
            raise ApiConfigurationError("Internal server error")

        if select_by_pattern := [
            response
            for response in integration_responses.values()
            if (selectionPatten := response.get("selectionPattern"))
            and re.match(selectionPatten, selection_value)
        ]:
            selected_response = select_by_pattern[0]
            if len(select_by_pattern) > 1:
                LOG.warning(
                    "Multiple integration responses matching '%s' statuscode. Choosing '%s' (first).",
                    selection_value,
                    selected_response["statusCode"],
                )
        else:
            # choose default return code
            # TODO: the provider should check this, as we should only have one default with no value in selectionPattern
            default_responses = [
                response
                for response in integration_responses.values()
                if not response.get("selectionPattern")
            ]
            if not default_responses:
                # TODO: verify log message when the selection_value is a lambda errorMessage
                LOG.warning(
                    "Configuration error: No match for output mapping and no default output mapping configured. "
                    "Endpoint Response Status Code: %s",
                    selection_value,
                )
                raise ApiConfigurationError("Internal server error")

            selected_response = default_responses[0]
            if len(default_responses) > 1:
                LOG.warning(
                    "Multiple default integration responses. Choosing %s (first).",
                    selected_response["statusCode"],
                )
        return selected_response
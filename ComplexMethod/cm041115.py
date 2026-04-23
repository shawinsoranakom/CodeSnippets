def render(self, api_context: ApiInvocationContext, **kwargs) -> bytes | str:
        # XXX: keep backwards compatibility until we migrate all integrations to this new classes
        # api_context contains a response object that we want slowly remove from it
        data = kwargs.get("response", "")
        response = data or api_context.response
        integration = api_context.integration
        # we set context data with the response content because later on we use context data as
        # the body field in the template. We need to improve this by using the right source
        # depending on the type of templates.
        api_context.data = response._content

        # status code returned by the integration
        status_code = str(response.status_code)

        # get the integration responses configuration from the integration object
        integration_responses = integration.get("integrationResponses")
        if not integration_responses:
            return response._content

        # get the configured integration response status codes,
        # e.g. ["200", "400", "500"]
        integration_status_codes = [str(code) for code in list(integration_responses.keys())]
        # if there are no integration responses, we return the response as is
        if not integration_status_codes:
            return response.content

        # The following code handles two use cases.If there is an integration response for the status code returned
        # by the integration, we use the template configured for that status code (1) or the errorMessage (2) for
        # lambda integrations.
        # For an HTTP integration, API Gateway matches the regex to the HTTP status code to return
        # For a Lambda function, API Gateway matches the regex to the errorMessage header to
        # return a status code.
        # For example, to set a 400 response for any error that starts with Malformed,
        # set the method response status code to 400 and the Lambda error regex to Malformed.*.
        match_resp = status_code
        if isinstance(try_json(response._content), dict):
            resp_dict = try_json(response._content)
            if "errorMessage" in resp_dict:
                match_resp = resp_dict.get("errorMessage")

        selected_integration_response = select_integration_response(match_resp, api_context)
        response.status_code = int(selected_integration_response.get("statusCode", 200))
        response_templates = selected_integration_response.get("responseTemplates", {})

        # we only support JSON and XML templates for now - if there is no template we return the response as is
        # If the content type is not supported we always use application/json as default value
        # TODO - support other content types, besides application/json and application/xml
        # see https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html#selecting-mapping-templates
        accept = api_context.headers.get("accept", APPLICATION_JSON)
        supported_types = [APPLICATION_JSON, APPLICATION_XML]
        media_type = accept if accept in supported_types else APPLICATION_JSON
        if not (template := response_templates.get(media_type, {})):
            return response._content

        # we render the template with the context data and the response content
        variables = self.build_variables_mapping(api_context)
        # update the response body
        response._content = self._render_as_text(template, variables)
        if media_type == APPLICATION_JSON:
            self._validate_json(response.content)
        elif media_type == APPLICATION_XML:
            self._validate_xml(response.content)

        if response_overrides := variables.get("context", {}).get("responseOverride", {}):
            response.headers.update(response_overrides.get("header", {}).items())
            response.status_code = response_overrides.get("status", 200)

        LOG.debug("Endpoint response body after transformations:\n%s", response._content)
        return response._content
def invoke(self, invocation_context: ApiInvocationContext):
        invocation_path = invocation_context.path_with_query_string
        integration = invocation_context.integration
        path_params = invocation_context.path_params
        method = invocation_context.method
        headers = invocation_context.headers

        relative_path, query_string_params = extract_query_string_params(path=invocation_path)
        uri = integration.get("uri") or integration.get("integrationUri") or ""

        # resolve integration parameters
        integration_parameters = self.request_params_resolver.resolve(context=invocation_context)
        headers.update(integration_parameters.get("headers", {}))
        self._set_http_apigw_headers(headers, invocation_context)

        if ":servicediscovery:" in uri:
            # check if this is a servicediscovery integration URI
            client = connect_to().servicediscovery
            service_id = uri.split("/")[-1]
            instances = client.list_instances(ServiceId=service_id)["Instances"]
            instance = (instances or [None])[0]
            if instance and instance.get("Id"):
                uri = "http://{}/{}".format(instance["Id"], invocation_path.lstrip("/"))

        # apply custom request template
        invocation_context.context = get_event_request_context(invocation_context)
        invocation_context.stage_variables = get_stage_variables(invocation_context)
        payload = self.request_templates.render(invocation_context)

        if isinstance(payload, dict):
            payload = json.dumps(payload)

        # https://docs.aws.amazon.com/apigateway/latest/developerguide/aws-api-gateway-stage-variables-reference.html
        # HTTP integration URIs
        #
        # A stage variable can be used as part of an HTTP integration URL, as shown in the following examples:
        #
        # A full URI without protocol – http://${stageVariables.<variable_name>}
        # A full domain – http://${stageVariables.<variable_name>}/resource/operation
        # A subdomain – http://${stageVariables.<variable_name>}.example.com/resource/operation
        # A path – http://example.com/${stageVariables.<variable_name>}/bar
        # A query string – http://example.com/foo?q=${stageVariables.<variable_name>}
        render_vars = {"stageVariables": invocation_context.stage_variables}
        rendered_uri = VtlTemplate().render_vtl(uri, render_vars)

        uri = apply_request_parameters(
            rendered_uri,
            integration=integration,
            path_params=path_params,
            query_params=query_string_params,
        )
        result = requests.request(method=method, url=uri, data=payload, headers=headers)
        if not result.ok:
            LOG.debug(
                "Upstream response from <%s> %s returned with status code: %s",
                method,
                uri,
                result.status_code,
            )
        # apply custom response template for non-proxy integration
        invocation_context.response = result
        if integration["type"] != "HTTP_PROXY":
            self.response_templates.render(invocation_context)
        return invocation_context.response
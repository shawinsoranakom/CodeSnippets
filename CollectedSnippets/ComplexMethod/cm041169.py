def invoke(self, context: RestApiInvocationContext) -> EndpointResponse:
        integration_req: IntegrationRequest = context.integration_request
        method = integration_req["http_method"]
        parsed_uri = self.parse_aws_integration_uri(integration_req["uri"])
        service_name = parsed_uri["service_name"]
        integration_region = parsed_uri["region_name"]

        if credentials := context.integration.get("credentials"):
            credentials = render_uri_with_stage_variables(credentials, context.stage_variables)

        headers = integration_req["headers"]
        # Some integrations will use a special format for the service in the URI, like AppSync, and so those requests
        # are not directed to a service directly, so need to add the Authorization header. It would fail parsing
        # by our service name parser anyway
        if service_name in self._service_names:
            headers.update(
                get_internal_mocked_headers(
                    service_name=service_name,
                    region_name=integration_region,
                    source_arn=get_source_arn(context),
                    role_arn=credentials,
                )
            )
        query_params = integration_req["query_string_parameters"].copy()
        data = integration_req["body"]

        if parsed_uri["action_type"] == "path":
            # the Path action type allows you to override the path the request is sent to, like you would send to AWS
            path = f"/{parsed_uri['path']}"
        else:
            # Action passes the `Action` query string parameter
            path = ""
            action = parsed_uri["path"]

            if target := self.get_action_service_target(service_name, action):
                # TODO: properly implement the auto-`Content-Type` headers depending on the service protocol
                #  e.g. `x-amz-json-1.0` for DynamoDB
                #  this is needed to properly support multi-protocol
                headers["X-Amz-Target"] = target

            query_params["Action"] = action

            if service_name in self.SERVICES_LEGACY_QUERY_PROTOCOL:
                # this has been tested in AWS: for `ssm`, it fully overrides the body because SSM uses the Query
                # protocol, so we simulate it that way
                data = self.get_payload_from_query_string(query_params)

        url = f"{self._base_domain}{path}"
        headers["Host"] = self.get_internal_host_for_service(
            service_name=service_name, region_name=integration_region
        )

        request_parameters = {
            "method": method,
            "url": url,
            "params": query_params,
            "headers": headers,
        }

        if method not in NO_BODY_METHODS:
            request_parameters["data"] = data

        request_response = requests.request(**request_parameters)
        response_content = request_response.content

        if (
            parsed_uri["action_type"] == "action"
            and service_name in self.SERVICES_LEGACY_QUERY_PROTOCOL
        ):
            response_content = self.format_response_content_legacy(
                payload=response_content,
                service_name=service_name,
                action=parsed_uri["path"],
                request_id=context.context_variables["requestId"],
            )

        return EndpointResponse(
            body=response_content,
            status_code=request_response.status_code,
            headers=Headers(dict(request_response.headers)),
        )
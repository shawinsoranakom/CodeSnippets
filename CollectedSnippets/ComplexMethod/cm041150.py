def invoke(self, invocation_context: ApiInvocationContext):
        integration = invocation_context.integration
        integration_type_orig = integration.get("type") or integration.get("integrationType") or ""
        integration_type = integration_type_orig.upper()
        uri = integration.get("uri") or integration.get("integrationUri") or ""
        integration_subtype = integration.get("integrationSubtype")

        if uri.endswith("kinesis:action/PutRecord") or integration_subtype == "Kinesis-PutRecord":
            target = "Kinesis_20131202.PutRecord"
        elif uri.endswith("kinesis:action/PutRecords"):
            target = "Kinesis_20131202.PutRecords"
        elif uri.endswith("kinesis:action/ListStreams"):
            target = "Kinesis_20131202.ListStreams"
        else:
            LOG.info(
                "Unexpected API Gateway integration URI '%s' for integration type %s",
                uri,
                integration_type,
            )
            target = ""

        try:
            # xXx this "event" request context is used in multiple places, we probably
            # want to refactor this into a model class.
            # I'd argue we should not make a decision on the event_request_context inside the integration because,
            # it's different between API types (REST, HTTP, WebSocket) and per event version
            invocation_context.context = get_event_request_context(invocation_context)
            invocation_context.stage_variables = get_stage_variables(invocation_context)

            # integration type "AWS" is only supported for WebSocket APIs and REST
            # API (v1), but the template selection expression is only supported for
            # Websockets
            if invocation_context.is_websocket_request():
                template_key = self.render_template_selection_expression(invocation_context)
                payload = self.request_templates.render(invocation_context, template_key)
            else:
                # For HTTP APIs with a specified integration_subtype,
                # a key-value map specifying parameters that are passed to AWS_PROXY integrations
                if integration_type == "AWS_PROXY" and integration_subtype == "Kinesis-PutRecord":
                    payload = self._create_request_parameters(invocation_context)
                else:
                    payload = self.request_templates.render(invocation_context)

        except Exception as e:
            LOG.warning("Unable to convert API Gateway payload to str", e)
            raise

        # forward records to target kinesis stream
        headers = get_internal_mocked_headers(
            service_name="kinesis",
            region_name=invocation_context.region_name,
            role_arn=invocation_context.integration.get("credentials"),
            source_arn=get_source_arn(invocation_context),
        )
        headers["X-Amz-Target"] = target

        result = common.make_http_request(
            url=config.internal_service_url(), data=payload, headers=headers, method="POST"
        )

        # apply response template
        invocation_context.response = result
        self.response_templates.render(invocation_context)
        return invocation_context.response
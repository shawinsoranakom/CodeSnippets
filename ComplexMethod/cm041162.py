def get_request_template(integration: Integration, request: InvocationRequest) -> str:
        """
        Attempts to return the request template.
        Will raise UnsupportedMediaTypeError if there are no match according to passthrough behavior.
        """
        request_templates = integration.get("requestTemplates") or {}
        passthrough_behavior = integration.get("passthroughBehavior")
        # If content-type is not provided aws assumes application/json
        content_type = request["headers"].get("Content-Type", APPLICATION_JSON)
        # first look to for a template associated to the content-type, otherwise look for the $default template
        request_template = request_templates.get(content_type) or request_templates.get("$default")

        if request_template or passthrough_behavior == PassthroughBehavior.WHEN_NO_MATCH:
            return request_template

        match passthrough_behavior:
            case PassthroughBehavior.NEVER:
                LOG.debug(
                    "No request template found for '%s' and passthrough behavior set to NEVER",
                    content_type,
                )
                raise UnsupportedMediaTypeError("Unsupported Media Type")
            case PassthroughBehavior.WHEN_NO_TEMPLATES:
                if request_templates:
                    LOG.debug(
                        "No request template found for '%s' and passthrough behavior set to WHEN_NO_TEMPLATES",
                        content_type,
                    )
                    raise UnsupportedMediaTypeError("Unsupported Media Type")
            case _:
                LOG.debug("Unknown passthrough behavior: '%s'", passthrough_behavior)

        return request_template
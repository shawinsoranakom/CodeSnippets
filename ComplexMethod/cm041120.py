def method_request_dict(self, context: ApiInvocationContext) -> dict[str, Any]:
        """
        Build a dict with all method request parameters and their values.
        :return: dict with all method request parameters and their values,
        and all keys in lowercase
        """
        params: dict[str, str] = {}

        # TODO: add support for multi-values headers and multi-values querystring

        for k, v in context.query_params().items():
            params[f"method.request.querystring.{k}"] = v

        for k, v in context.headers.items():
            params[f"method.request.header.{k}"] = v

        for k, v in context.path_params.items():
            params[f"method.request.path.{k}"] = v

        for k, v in context.stage_variables.items():
            params[f"stagevariables.{k}"] = v

        # TODO: add support for missing context variables, use `context.context` which contains most of the variables
        #  see https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-mapping-template-reference.html#context-variable-reference
        #  - all `context.identity` fields
        #  - protocol
        #  - requestId, extendedRequestId
        #  - all requestOverride, responseOverride
        #  - requestTime, requestTimeEpoch
        #  - resourcePath
        #  - wafResponseCode, webaclArn
        params["context.accountId"] = context.account_id
        params["context.apiId"] = context.api_id
        params["context.domainName"] = context.domain_name
        params["context.httpMethod"] = context.method
        params["context.path"] = context.path
        params["context.resourceId"] = context.resource_id
        params["context.stage"] = context.stage

        auth_context_authorizer = context.auth_context.get("authorizer") or {}
        for k, v in auth_context_authorizer.items():
            if isinstance(v, bool):
                v = canonicalize_bool_to_str(v)
            elif is_number(v):
                v = str(v)

            params[f"context.authorizer.{k.lower()}"] = v

        if context.data:
            params["method.request.body"] = context.data

        return {key.lower(): val for key, val in params.items()}
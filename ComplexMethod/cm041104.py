def _add_paths(self, spec, resources, with_extension):
        for item in resources.get("items"):
            path = item.get("path")
            for method, method_config in item.get("resourceMethods", {}).items():
                method = method.lower()

                method_integration = method_config.get("methodIntegration", {})
                integration_responses = method_integration.get("integrationResponses", {})
                method_responses = method_config.get("methodResponses")
                responses = {}
                produces = set()
                for status_code, values in method_responses.items():
                    response = {"description": f"{status_code} response"}
                    content = {}
                    if response_parameters := values.get("responseParameters"):
                        headers = {}
                        for parameter in response_parameters:
                            in_, name = parameter.removeprefix("method.response.").split(".")
                            # TODO: other type? query?
                            if in_ == "header":
                                headers[name] = {"schema": {"type": "string"}}

                        if headers:
                            response["headers"] = headers
                    if response_models := values.get("responseModels"):
                        for content_type, model_name in response_models.items():
                            content[content_type] = {
                                "schema": {"$ref": f"#/components/schemas/{model_name}"}
                            }
                    if integration_response := integration_responses.get(status_code, {}):
                        produces.update(integration_response.get("responseTemplates", {}).keys())

                    response["content"] = content
                    responses[status_code] = response

                request_parameters = method_config.get("requestParameters", {})
                parameters = []
                for parameter, required in request_parameters.items():
                    in_, name = parameter.removeprefix("method.request.").split(".")
                    in_ = in_ if in_ != "querystring" else "query"
                    parameters.append({"name": name, "in": in_, "schema": {"type": "string"}})

                request_body = {"content": {}}
                request_models = method_config.get("requestModels", {})
                for content_type, model_name in request_models.items():
                    request_body["content"][content_type] = {
                        "schema": {"$ref": f"#/components/schemas/{model_name}"},
                    }
                    request_body["required"] = True

                method_operations = {"responses": responses}
                if parameters:
                    method_operations["parameters"] = parameters
                if request_body["content"]:
                    method_operations["requestBody"] = request_body
                if operation_name := method_config.get("operationName"):
                    method_operations["operationId"] = operation_name
                if with_extension and method_integration:
                    method_operations[OpenAPIExt.INTEGRATION] = self._get_integration(
                        method_integration
                    )

                spec.path(path=path, operations={method: method_operations})
def generate_docs(self, format, method, schema) -> dict:
        if not self._is_method_exposed(method):
            return {}
        if method.upper() == "GET":
            # Get requests receive parameters from CGI, so their schema description
            # is a bit different from the POST / PUT / PATCH
            endpoint_description = {
                "parameters": self._construct_openapi_get_request_schema(schema),
                # disable yaml optimization to avoid
                # "instance type (string) does not match any allowed primitive type"
                # error from openapi validator
                "responses": copy.deepcopy(self.DEFAULT_RESPONSES_DESCRIPTION),
            }
        else:
            if format == "raw":
                content_header = "text/plain"
                openapi_schema = self._construct_openapi_plaintext_schema(schema)
            elif format == "custom":
                content_header = "application/json"
                openapi_schema = self._construct_openapi_json_schema(schema)
            else:
                raise ValueError(f"Unknown endpoint input format: {format}")
            schema_and_examples = {"schema": openapi_schema}
            if self.examples:
                schema_and_examples["examples"] = self.examples._openapi_description()
            content_description = {content_header: schema_and_examples}
            endpoint_description = {
                "requestBody": {
                    "content": content_description,
                },
                # disable yaml optimization to avoid
                # "instance type (string) does not match any allowed primitive type"
                # error from openapi validator
                "responses": copy.deepcopy(self.DEFAULT_RESPONSES_DESCRIPTION),
            }

        if self.tags is not None:
            endpoint_description["tags"] = list(self.tags)
        if self.description is not None:
            endpoint_description["description"] = self.description
        if self.summary is not None:
            endpoint_description["summary"] = self.summary

        return {method.lower(): endpoint_description}
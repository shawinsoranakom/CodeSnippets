def _parse_shape(
        self, request: Request, shape: Shape, node: Any, uri_params: Mapping[str, Any] = None
    ) -> Any:
        """
        Main parsing method which dynamically calls the parsing function for the specific shape.

        :param request: the complete Request
        :param shape: of the node
        :param node: the single part of the HTTP request to parse
        :param uri_params: the extracted URI path params
        :return: result of the parsing operation, the type depends on the shape
        """
        if shape is None:
            return None
        location = shape.serialization.get("location")
        if location is not None:
            if location == "header":
                header_name = shape.serialization.get("name")
                if shape.type_name == "list":
                    # headers may contain a comma separated list of values (e.g., the ObjectAttributes member in
                    # s3.GetObjectAttributes), so we prepare it here for the handler, which will be `_parse_list`.
                    # Header lists can contain optional whitespace, so we strip it
                    # https://www.rfc-editor.org/rfc/rfc9110.html#name-lists-rule-abnf-extension
                    # It can also directly contain a list of headers
                    # See https://datatracker.ietf.org/doc/html/rfc2616
                    payload = request.headers.getlist(header_name) or None
                    if payload:
                        headers = ",".join(payload)
                        payload = [value.strip() for value in headers.split(",")]

                else:
                    payload = request.headers.get(header_name)

            elif location == "headers":
                payload = self._parse_header_map(shape, request.headers)
                # shapes with the location trait "headers" only contain strings and are not further processed
                return payload
            elif location == "querystring":
                query_name = shape.serialization.get("name")
                parsed_query = request.args
                if shape.type_name == "list":
                    payload = parsed_query.getlist(query_name)
                else:
                    payload = parsed_query.get(query_name)
            elif location == "uri":
                uri_param_name = shape.serialization.get("name")
                if uri_param_name in uri_params:
                    payload = uri_params[uri_param_name]
            else:
                raise UnknownParserError(f"Unknown shape location '{location}'.")
        else:
            # If we don't have to use a specific location, we use the node
            payload = node

        fn_name = f"_parse_{shape.type_name}"
        handler = getattr(self, fn_name, self._noop_parser)
        try:
            return handler(request, shape, payload, uri_params) if payload is not None else None
        except (TypeError, ValueError, AttributeError) as e:
            raise ProtocolParserError(
                f"Invalid type when parsing {shape.name}: '{payload}' cannot be parsed to {shape.type_name}."
            ) from e
def _parse_payload(
        self,
        request: Request,
        shape: Shape,
        member_shapes: dict[str, Shape],
        uri_params: Mapping[str, Any],
        final_parsed: dict,
    ) -> None:
        """Parses all attributes which are located in the payload / body of the incoming request."""
        payload_parsed = {}
        non_payload_parsed = {}
        if "payload" in shape.serialization:
            # If a payload is specified in the output shape, then only that shape is used for the body payload.
            payload_member_name = shape.serialization["payload"]
            body_shape = member_shapes[payload_member_name]
            if body_shape.serialization.get("eventstream"):
                body = self._create_event_stream(request, body_shape)
                payload_parsed[payload_member_name] = body
            elif body_shape.type_name == "string":
                # Only set the value if it's not empty (the request's data is an empty binary by default)
                if request.data:
                    body = request.data
                    if isinstance(body, bytes):
                        body = body.decode(self.DEFAULT_ENCODING)
                    payload_parsed[payload_member_name] = body
            elif body_shape.type_name == "blob":
                # This control path is equivalent to operation.has_streaming_input (shape has a payload which is a blob)
                # in which case we assume essentially an IO[bytes] to be passed. Since the payload can be optional, we
                # only set the parameter if content_length=0, which indicates an empty request. If the content length is
                # not set, it could be a streaming response.
                if request.content_length != 0:
                    payload_parsed[payload_member_name] = self.create_input_stream(request)
            else:
                original_parsed = self._initial_body_parse(request)
                payload_parsed[payload_member_name] = self._parse_shape(
                    request, body_shape, original_parsed, uri_params
                )
        else:
            # The payload covers the whole body. We only parse the body if it hasn't been handled by the payload logic.
            try:
                non_payload_parsed = self._initial_body_parse(request)
            except ProtocolParserError:
                # GET requests should ignore the body, so we just let them pass
                if not (request.method in ["GET", "HEAD"] and self.ignore_get_body_errors):
                    raise

        # even if the payload has been parsed, the rest of the shape needs to be processed as well
        # (for members which are located outside of the body, like uri or header)
        non_payload_parsed = self._parse_shape(request, shape, non_payload_parsed, uri_params)
        # update the final result with the parsed body and the parsed payload (where the payload has precedence)
        final_parsed.update(non_payload_parsed)
        final_parsed.update(payload_parsed)
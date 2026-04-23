def _serialize_error(
        self,
        error: ServiceException,
        response: Response,
        shape: StructureShape,
        operation_model: OperationModel,
        mime_type: str,
        request_id: str,
    ) -> None:
        body = {}

        # TODO implement different service-specific serializer configurations
        #   - currently we set both, the `__type` member as well as the `X-Amzn-Errortype` header
        #   - the specification defines that it's either the __type field OR the header
        # this depends on the JSON protocol version as well. If json-1.0 the Error should be the full shape ID, like
        # com.amazon.coral.service#ExceptionName
        # if json-1.1, it should only be the name

        is_query_compatible = operation_model.service_model.is_query_compatible
        code = self._get_error_code(is_query_compatible, error, shape)

        response.headers["X-Amzn-Errortype"] = code

        # the `__type` field is not defined in default botocore error shapes
        body["__type"] = code

        if shape:
            remaining_params = {}
            # TODO add a possibility to serialize simple non-modelled errors (like S3 NoSuchBucket#BucketName)
            for member in shape.members:
                if hasattr(error, member):
                    value = getattr(error, member)

                # Default error message fields can sometimes have different casing in the specs
                elif member.lower() in ["code", "message"] and hasattr(error, member.lower()):
                    value = getattr(error, member.lower())

                else:
                    continue

                if value is None:
                    # do not serialize a value that is set to `None`
                    continue

                # if the value is falsy (empty string, empty list) and not in the Shape required members, AWS will
                # not serialize it, and it will not be part of the response body.
                if value or member in shape.required_members:
                    remaining_params[member] = value

            self._serialize(body, remaining_params, shape, None, mime_type)

        # this is a workaround, some Error Shape do not define a `Message` field, but it is always returned
        # this could be solved at the same time as the `__type` field
        if "message" not in body and "Message" not in body:
            if error_message := self._get_error_message(error):
                body["message"] = error_message

        if mime_type in self.CBOR_TYPES:
            response.set_response(cbor2_dumps(body, datetime_as_timestamp=True))
            response.content_type = mime_type
        else:
            response.set_json(body)

        if is_query_compatible:
            self._add_query_compatible_error_header(response, error)
def _serialize_error_structure(
        self, body: bytearray, shape: Shape | None, error: ServiceException, code: str
    ):
        if not shape:
            shape = self._DEFAULT_ERROR_STRUCTURE_SHAPE
            shape_members = shape.members
        else:
            # we need to manually add the `__type` field to the shape members as it is not part of the specs
            # we do a shallow copy of the shape members
            shape_members = shape.members.copy()
            shape_members["__type"] = self._ERROR_TYPE_SHAPE

        # Error responses in the rpcv2Cbor protocol MUST be serialized identically to standard responses with one
        # additional component to distinguish which error is contained: a body field named __type.
        params = {"__type": code}

        for member in shape_members:
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
                params[member] = value

        self._serialize_type_structure(body, params, shape, None, shape_members=shape_members)
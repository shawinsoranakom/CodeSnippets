def _serialize_type_structure(
        self, body: dict, value: dict, shape: StructureShape, key: str | None, mime_type: str
    ):
        if value is None:
            return
        if shape.is_document_type:
            body[key] = value
        else:
            if key is not None:
                # If a key is provided, this is a result of a recursive
                # call, so we need to add a new child dict as the value
                # of the passed in serialized dict.  We'll then add
                # all the structure members as key/vals in the new serialized
                # dictionary we just created.
                new_serialized = {}
                body[key] = new_serialized
                body = new_serialized
            members = shape.members
            for member_key, member_value in value.items():
                if member_value is None:
                    continue
                try:
                    member_shape = members[member_key]
                except KeyError:
                    LOG.warning(
                        "Response object %s contains a member which is not specified: %s",
                        shape.name,
                        member_key,
                    )
                    continue
                if "name" in member_shape.serialization:
                    member_key = member_shape.serialization["name"]
                self._serialize(body, member_value, member_shape, member_key, mime_type)
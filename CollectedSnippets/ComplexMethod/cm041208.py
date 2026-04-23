def _parse_structure(
        self,
        request: Request,
        shape: StructureShape,
        node: dict | None,
        uri_params: Mapping[str, Any] = None,
    ):
        if shape.is_document_type:
            final_parsed = node
        else:
            if node is None:
                # If the comes across the wire as "null" (None in python),
                # we should be returning this unchanged, instead of as an
                # empty dict.
                return None
            final_parsed = {}
            members = shape.members
            if shape.is_tagged_union:
                cleaned_value = node.copy()
                cleaned_value.pop("__type", None)
                cleaned_value = {k: v for k, v in cleaned_value.items() if v is not None}
                if len(cleaned_value) != 1:
                    raise ProtocolParserError(
                        f"Invalid service response: {shape.name} must have one and only one member set."
                    )

            for member_name, member_shape in members.items():
                member_value = node.get(member_name)
                if member_value is not None:
                    final_parsed[member_name] = self._parse_shape(
                        request, member_shape, member_value, uri_params
                    )

        return final_parsed
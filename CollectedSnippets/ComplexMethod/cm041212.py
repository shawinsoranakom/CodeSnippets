def _process_header_members(self, parameters: dict, response: Response, shape: Shape):
        shape_members = shape.members if isinstance(shape, StructureShape) else []
        for name in shape_members:
            member_shape = shape_members[name]
            location = member_shape.serialization.get("location")
            if not location:
                continue
            if name not in parameters:
                # ignores optional keys
                continue
            key = member_shape.serialization.get("name", name)
            value = parameters[name]
            if value is None:
                continue
            if location == "header":
                response.headers[key] = self._serialize_header_value(member_shape, value)
            elif location == "headers":
                header_prefix = key
                self._serialize_header_map(header_prefix, response, value)
            elif location == "statusCode":
                response.status_code = int(value)
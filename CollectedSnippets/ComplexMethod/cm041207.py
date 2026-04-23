def _parse_structure(
        self,
        request: Request,
        shape: StructureShape,
        node: ETree.Element,
        uri_params: Mapping[str, Any] = None,
    ) -> dict:
        parsed = {}
        xml_dict = self._build_name_to_xml_node(node)
        for member_name, member_shape in shape.members.items():
            xml_name = self._member_key_name(member_shape, member_name)
            member_node = xml_dict.get(xml_name)
            # If a shape defines a location trait, the node might be None (since these are extracted from the request's
            # metadata like headers or the URI)
            if (
                member_node is not None
                or "location" in member_shape.serialization
                or member_shape.serialization.get("eventheader")
            ):
                parsed[member_name] = self._parse_shape(
                    request, member_shape, member_node, uri_params
                )
            elif member_shape.serialization.get("xmlAttribute"):
                attributes = {}
                location_name = member_shape.serialization["name"]
                for key, value in node.attrib.items():
                    new_key = self._namespace_re.sub(location_name.split(":")[0] + ":", key)
                    attributes[new_key] = value
                if location_name in attributes:
                    parsed[member_name] = attributes[location_name]
            elif member_name in shape.required_members:
                # If the member is required, but not existing, we explicitly set None
                parsed[member_name] = None
        return parsed
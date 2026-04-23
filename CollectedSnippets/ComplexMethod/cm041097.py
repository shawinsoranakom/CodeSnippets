def _resolve_intrinsic_function_fn_get_att(self, arguments: ChangeSetEntity) -> ChangeType:
        # TODO: add support for nested intrinsic functions.
        # TODO: validate arguments structure and type.
        # TODO: should this check for deletion of resources and/or properties, if so what error should be raised?

        if not isinstance(arguments, NodeArray) or not arguments.array:
            raise RuntimeError()
        logical_name_of_resource_entity = arguments.array[0]
        if not isinstance(logical_name_of_resource_entity, TerminalValue):
            raise RuntimeError()
        logical_name_of_resource: str = logical_name_of_resource_entity.value
        if not isinstance(logical_name_of_resource, str):
            raise RuntimeError()
        node_resource: NodeResource = self._retrieve_or_visit_resource(
            resource_name=logical_name_of_resource
        )

        node_property_attribute_name = arguments.array[1]
        if not isinstance(node_property_attribute_name, TerminalValue):
            raise RuntimeError()
        if isinstance(node_property_attribute_name, TerminalValueModified):
            attribute_name = node_property_attribute_name.modified_value
        else:
            attribute_name = node_property_attribute_name.value

        # TODO: this is another use case for which properties should be referenced by name
        for node_property in node_resource.properties.properties:
            if node_property.name == attribute_name:
                return node_property.change_type

        return ChangeType.UNCHANGED
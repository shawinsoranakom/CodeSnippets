def visit_node_properties(
        self, node_properties: NodeProperties
    ) -> PreprocEntityDelta[PreprocProperties, PreprocProperties]:
        node_change_type = node_properties.change_type
        before_bindings = {} if node_change_type != ChangeType.CREATED else Nothing
        after_bindings = {} if node_change_type != ChangeType.REMOVED else Nothing
        for node_property in node_properties.properties:
            property_name = node_property.name
            delta = self.visit(node_property)
            delta_before = delta.before
            delta_after = delta.after
            if (
                not is_nothing(before_bindings)
                and not is_nothing(delta_before)
                and delta_before is not None
            ):
                before_bindings[property_name] = delta_before
            if (
                not is_nothing(after_bindings)
                and not is_nothing(delta_after)
                and delta_after is not None
            ):
                after_bindings[property_name] = delta_after
        before = Nothing
        if not is_nothing(before_bindings):
            before = PreprocProperties(properties=before_bindings)
        after = Nothing
        if not is_nothing(after_bindings):
            after = PreprocProperties(properties=after_bindings)
        return PreprocEntityDelta(before=before, after=after)
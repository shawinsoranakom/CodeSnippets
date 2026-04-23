def _resolve_attribute(self, arguments: str | list[str], select_before: bool) -> str:
        # TODO: add arguments validation.
        arguments_list: list[str]
        if isinstance(arguments, str):
            arguments_list = arguments.split(".")
        else:
            arguments_list = arguments

        if len(arguments_list) < 2:
            raise ValidationError(
                "Template error: every Fn::GetAtt object requires two non-empty parameters, the resource name and the resource attribute"
            )

        logical_name_of_resource = arguments_list[0]
        attribute_name = ".".join(arguments_list[1:])

        node_resource = self._get_node_resource_for(
            resource_name=logical_name_of_resource,
            node_template=self._change_set.update_model.node_template,
        )

        if not is_nothing(node_resource.condition_reference):
            condition = self._get_node_condition_if_exists(node_resource.condition_reference.value)
            evaluation_result = self._resolve_condition(condition.name)

            if select_before and not evaluation_result.before:
                raise ValidationError(
                    f"Template format error: Unresolved resource dependencies [{logical_name_of_resource}] in the Resources block of the template"
                )

            if not select_before and not evaluation_result.after:
                raise ValidationError(
                    f"Template format error: Unresolved resource dependencies [{logical_name_of_resource}] in the Resources block of the template"
                )

        # Custom Resources can mutate their definition
        # So the preproc should search first in the resource values and then check the template
        if select_before:
            value = self._before_deployed_property_value_of(
                resource_logical_id=logical_name_of_resource,
                property_name=attribute_name,
            )
        else:
            value = self._after_deployed_property_value_of(
                resource_logical_id=logical_name_of_resource,
                property_name=attribute_name,
            )
        if value is not None:
            return value

        node_property: NodeProperty | None = self._get_node_property_for(
            property_name=attribute_name, node_resource=node_resource
        )
        if node_property is not None:
            # The property is statically defined in the template and its value can be computed.
            property_delta = self.visit(node_property)
            value = property_delta.before if select_before else property_delta.after

        return value
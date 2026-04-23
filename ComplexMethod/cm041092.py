def _register_resource_change(
        self,
        logical_id: str,
        type_: str,
        physical_id: str | None,
        before_properties: PreprocProperties | None,
        after_properties: PreprocProperties | None,
        # TODO: remove default
        requires_replacement: bool = False,
    ) -> None:
        action = cfn_api.ChangeAction.Modify
        if before_properties is None:
            action = cfn_api.ChangeAction.Add
        elif after_properties is None:
            action = cfn_api.ChangeAction.Remove

        resource_change = cfn_api.ResourceChange()
        resource_change["Action"] = action
        resource_change["LogicalResourceId"] = logical_id
        resource_change["ResourceType"] = type_
        if physical_id:
            resource_change["PhysicalResourceId"] = physical_id
        if self._include_property_values:
            if before_properties is not None:
                before_context_properties = {PropertiesKey: before_properties.properties}
                before_context_properties_json_str = json.dumps(before_context_properties)
                resource_change["BeforeContext"] = before_context_properties_json_str

            if after_properties is not None:
                after_context_properties = {PropertiesKey: after_properties.properties}
                after_context_properties_json_str = json.dumps(after_context_properties)
                resource_change["AfterContext"] = after_context_properties_json_str

        if action == cfn_api.ChangeAction.Modify:
            # TODO: handle "Conditional" case
            resource_change["Replacement"] = (
                Replacement.True_ if requires_replacement else Replacement.False_
            )

        self._changes.append(
            cfn_api.Change(Type=cfn_api.ChangeType.Resource, ResourceChange=resource_change)
        )
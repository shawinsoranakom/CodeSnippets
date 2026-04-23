def resource_config_differs(self, resource_new):
        """Return whether the given resource properties differ from the existing config (for stack updates)."""
        # TODO: this is broken for default fields and result_handler property modifications when they're added to the properties in the model
        resource_id = resource_new["LogicalResourceId"]
        resource_old = self.resources[resource_id]
        props_old = resource_old.get("SpecifiedProperties", {})
        props_new = resource_new["Properties"]
        ignored_keys = ["LogicalResourceId", "PhysicalResourceId"]
        old_keys = set(props_old.keys()) - set(ignored_keys)
        new_keys = set(props_new.keys()) - set(ignored_keys)
        if old_keys != new_keys:
            return True
        for key in old_keys:
            if props_old[key] != props_new[key]:
                return True
        old_status = self.stack.resource_states.get(resource_id) or {}
        previous_state = (
            old_status.get("PreviousResourceStatus") or old_status.get("ResourceStatus") or ""
        )
        if old_status and "DELETE" in previous_state:
            return True
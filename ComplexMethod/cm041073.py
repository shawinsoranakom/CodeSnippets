def _set_resource_status_details(self, resource_id: str, physical_res_id: str = None):
        """Helper function to ensure that the status details for the given resource ID are up-to-date."""
        resource = self.resources.get(resource_id)
        if resource is None or resource.get("Type") == "Parameter":
            # make sure we delete the states for any non-existing/deleted resources
            self._resource_states.pop(resource_id, None)
            return
        state = self._resource_states.setdefault(resource_id, {})
        attr_defaults = (
            ("LogicalResourceId", resource_id),
            ("PhysicalResourceId", physical_res_id),
        )
        for res in [resource, state]:
            for attr, default in attr_defaults:
                res[attr] = res.get(attr) or default
        state["StackName"] = state.get("StackName") or self.stack_name
        state["StackId"] = state.get("StackId") or self.stack_id
        state["ResourceType"] = state.get("ResourceType") or self.resources[resource_id].get("Type")
        state["Timestamp"] = timestamp_millis()
        return state
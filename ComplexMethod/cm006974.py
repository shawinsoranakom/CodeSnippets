def build_tool(self) -> Sequence[Tool]:
        """Build Composio tools based on selected actions.

        Returns:
            Sequence[Tool]: List of configured Composio tools.
        """
        # Check if we're in Astra cloud environment and raise an error if we are.
        raise_error_if_astra_cloud_disable_component(disable_component_in_astra_cloud_msg)
        composio = self._build_wrapper()
        action_names = [action["name"] for action in self.actions]

        # Get toolkits from action names
        toolkits = set()
        for action_name in action_names:
            if "_" in action_name:
                toolkit = action_name.split("_")[0].lower()
                toolkits.add(toolkit)

        if not toolkits:
            return []

        # Get all tools for the relevant toolkits
        all_tools = composio.tools.get(user_id=self.entity_id, toolkits=list(toolkits))

        # Filter to only the specific actions we want using list comprehension
        return [tool for tool in all_tools if hasattr(tool, "name") and tool.name in action_names]
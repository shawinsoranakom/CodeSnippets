def _filter_tools_by_status(self, tools: list[Tool], metadata: pd.DataFrame | None) -> list[Tool]:
        """Filter tools based on their status in metadata.

        Args:
            tools (list[Tool]): List of tools to filter.
            metadata (list[dict] | None): Tools metadata containing status information.

        Returns:
            list[Tool]: Filtered list of tools.
        """
        # Convert metadata to a list of dicts if it's a DataFrame
        metadata_dict = None  # Initialize as None to avoid lint issues with empty dict
        if isinstance(metadata, pd.DataFrame):
            metadata_dict = metadata.to_dict(orient="records")

        # If metadata is None or empty, use enabled_tools
        if not metadata_dict:
            enabled = self.enabled_tools
            return (
                tools
                if enabled is None
                else [
                    tool for tool in tools if any(enabled_name in [tool.name, *tool.tags] for enabled_name in enabled)
                ]
            )

        # Ensure metadata is a list of dicts
        if not isinstance(metadata_dict, list):
            return tools

        # Create a mapping of tool names to their status
        tool_status = {item["name"]: item.get("status", True) for item in metadata_dict}
        return [tool for tool in tools if tool_status.get(tool.name, True)]
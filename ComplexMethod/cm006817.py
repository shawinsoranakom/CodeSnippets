async def update_outputs(self, frontend_node: dict, field_name: str, field_value: Any) -> dict:
        """Update the outputs of the frontend node.

        This method is called when the flow_name_selected field is updated.
        It will generate the Output objects for the selected flow and update the outputs of the frontend node.

        Args:
            frontend_node: The frontend node to update the outputs for.
            field_name: The name of the field that was updated.
            field_value: The value of the field that was updated.

        Returns:
            The updated frontend node.
        """
        if (field_name == "flow_name_selected" and field_value) or (
            field_name == "tool_mode" and not field_value
        ):  # display selected flow's outputs when selected or tool_mode is turned off
            selected_flow = frontend_node.get("template", {}).get("flow_name_selected", {})
            selected_flow_meta = selected_flow.get("selected_metadata", {})
            if flow_name := (field_value if field_name == "flow_name_selected" else selected_flow.get("value")):
                graph = await self.get_graph(
                    flow_name_selected=flow_name,
                    flow_id_selected=selected_flow_meta.get("id"),
                    updated_at=selected_flow_meta.get("updated_at"),
                )
                outputs = self._format_flow_outputs(graph)  # generate Output objects from the flow's output nodes
                self._sync_flow_outputs(outputs)
                frontend_node["outputs"] = [output.model_dump() for output in outputs]

        return frontend_node
async def run_and_validate_update_outputs(self, frontend_node: dict, field_name: str, field_value: Any):
        if inspect.iscoroutinefunction(self.update_outputs):
            frontend_node = await self.update_outputs(frontend_node, field_name, field_value)
        else:
            frontend_node = self.update_outputs(frontend_node, field_name, field_value)
        if field_name == "tool_mode" or frontend_node.get("tool_mode"):
            is_tool_mode = field_value or frontend_node.get("tool_mode")
            frontend_node["outputs"] = [self._build_tool_output()] if is_tool_mode else frontend_node["outputs"]
            if is_tool_mode:
                frontend_node.setdefault("template", {})
                frontend_node["tool_mode"] = True
                tools_metadata_input = await self._build_tools_metadata_input()
                frontend_node["template"][TOOLS_METADATA_INPUT_NAME] = tools_metadata_input.to_dict()
                self._append_tool_to_outputs_map()
            elif "template" in frontend_node:
                frontend_node["template"].pop(TOOLS_METADATA_INPUT_NAME, None)
        self.tools_metadata = frontend_node.get("template", {}).get(TOOLS_METADATA_INPUT_NAME, {}).get("value")
        return self._validate_frontend_node(frontend_node)
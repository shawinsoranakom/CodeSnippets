def validate_tool(self, build_config: dict, field_value: Any, tool_name: str | None = None) -> dict:
        # Get the index of the selected tool in the list of options
        selected_tool_index = next(
            (
                ind
                for ind, tool in enumerate(build_config["tool_name"]["options"])
                if tool["name"] == field_value
                or ("validate" in field_value and tool["name"] == field_value["validate"])
            ),
            None,
        )

        # Set the link to be the text 'validated'
        build_config["tool_name"]["options"][selected_tool_index]["link"] = "validated"

        # Set the helper text and helper text metadata field of the actions now
        build_config["actions"]["helper_text"] = ""
        build_config["actions"]["helper_text_metadata"] = {"icon": "Check", "variant": "success"}

        try:
            composio = self._build_wrapper()
            current_tool = tool_name or getattr(self, "tool_name", None)
            if not current_tool:
                self.log("No tool name available for validate_tool")
                return build_config

            toolkit_slug = current_tool.lower()

            tools = composio.tools.get(user_id=self.entity_id, toolkits=[toolkit_slug])

            authenticated_actions = []
            for tool in tools:
                if hasattr(tool, "name"):
                    action_name = tool.name
                    display_name = action_name.replace("_", " ").title()
                    authenticated_actions.append({"name": action_name, "display_name": display_name})
        except (ValueError, ConnectionError, AttributeError) as e:
            self.log(f"Error getting actions for {current_tool or 'unknown tool'}: {e}")
            authenticated_actions = []

        build_config["actions"]["options"] = [
            {
                "name": action["name"],
            }
            for action in authenticated_actions
        ]

        build_config["actions"]["show"] = True
        return build_config
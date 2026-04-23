async def _build_tools_metadata_input(self):
        try:
            from lfx.inputs.inputs import ToolsInput
        except ImportError as e:
            msg = "Failed to import ToolsInput from lfx.inputs.inputs"
            raise ImportError(msg) from e
        placeholder = None
        tools = []
        try:
            # Handle both sync and async _get_tools methods
            # TODO: this check can be remomved ince get tools is async
            if asyncio.iscoroutinefunction(self._get_tools):
                tools = await self._get_tools()
            else:
                tools = self._get_tools()

            placeholder = "Loading actions..." if len(tools) == 0 else ""
        except (TimeoutError, asyncio.TimeoutError):
            placeholder = "Timeout loading actions"
        except (ConnectionError, OSError, ValueError):
            placeholder = "Error loading actions"
        # Always use the latest tool data
        tool_data = [self._build_tool_data(tool) for tool in tools]
        # print(tool_data)
        if hasattr(self, TOOLS_METADATA_INPUT_NAME):
            old_tags = self._extract_tools_tags(self.tools_metadata)
            new_tags = self._extract_tools_tags(tool_data)
            if self.check_for_tool_tag_change(old_tags, new_tags):
                # If enabled tools are set, update status based on them
                enabled = self.enabled_tools
                if enabled is not None:
                    for item in tool_data:
                        item["status"] = any(enabled_name in [item["name"], *item["tags"]] for enabled_name in enabled)
                self.tools_metadata = tool_data
            else:
                # Preserve existing status values
                existing_status = {item["name"]: item.get("status", True) for item in self.tools_metadata}
                for item in tool_data:
                    item["status"] = existing_status.get(item["name"], True)
                tool_data = self.tools_metadata
        else:
            # If enabled tools are set, update status based on them
            enabled = self.enabled_tools
            if enabled is not None:
                for item in tool_data:
                    item["status"] = any(enabled_name in [item["name"], *item["tags"]] for enabled_name in enabled)
            self.tools_metadata = tool_data

        return ToolsInput(
            name=TOOLS_METADATA_INPUT_NAME,
            placeholder=placeholder,
            display_name="Actions",
            info=TOOLS_METADATA_INFO,
            value=tool_data,
        )
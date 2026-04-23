async def _update_tool_config(self, build_config: dict, tool_name: str) -> None:
        """Update tool configuration with proper error handling."""
        if not self.tools:
            self.tools, build_config["mcp_server"]["value"] = await self.update_tool_list()

        if not tool_name:
            return

        tool_obj = next((tool for tool in self.tools if tool.name == tool_name), None)
        if not tool_obj:
            msg = f"Tool {tool_name} not found in available tools: {self.tools}"
            self.remove_non_default_keys(build_config)
            build_config["tool"]["value"] = ""
            await logger.awarning(msg)
            return

        try:
            # Store current values before removing inputs (only for the current tool)
            current_values = {}
            for key, value in build_config.items():
                if key not in self.default_keys and isinstance(value, dict) and "value" in value:
                    current_values[key] = value["value"]

            # Remove ALL non-default keys (all previous tool inputs)
            self.remove_non_default_keys(build_config)

            # Get and validate new inputs for the selected tool
            self.schema_inputs = await self._validate_schema_inputs(tool_obj)
            if not self.schema_inputs:
                msg = f"No input parameters to configure for tool '{tool_name}'"
                await logger.ainfo(msg)
                return

            # Add new inputs to build config for the selected tool only
            for schema_input in self.schema_inputs:
                if not schema_input or not hasattr(schema_input, "name"):
                    msg = "Invalid schema input detected, skipping"
                    await logger.awarning(msg)
                    continue

                try:
                    name = schema_input.name
                    input_dict = schema_input.to_dict()
                    input_dict.setdefault("value", None)
                    input_dict.setdefault("required", True)

                    build_config[name] = input_dict

                    # Preserve existing value if the parameter name exists in current_values
                    if name in current_values:
                        build_config[name]["value"] = current_values[name]

                except (AttributeError, KeyError, TypeError) as e:
                    msg = f"Error processing schema input {schema_input}: {e!s}"
                    await logger.aexception(msg)
                    continue
        except ValueError as e:
            msg = f"Schema validation error for tool {tool_name}: {e!s}"
            await logger.aexception(msg)
            self.schema_inputs = []
            return
        except (AttributeError, KeyError, TypeError) as e:
            msg = f"Error updating tool config: {e!s}"
            await logger.aexception(msg)
            raise ValueError(msg) from e
def _register_tool_as_action(self, registry: Registry, action_name: str, tool: Any) -> None:
		"""Register a single MCP tool as a browser-use action.

		Args:
			registry: Browser-use registry to register action to
			action_name: Name for the registered action
			tool: MCP Tool object with schema information
		"""
		# Parse tool parameters to create Pydantic model
		param_fields = {}

		if tool.inputSchema:
			# MCP tools use JSON Schema for parameters
			properties = tool.inputSchema.get('properties', {})
			required = set(tool.inputSchema.get('required', []))

			for param_name, param_schema in properties.items():
				# Convert JSON Schema type to Python type
				param_type = self._json_schema_to_python_type(param_schema, f'{action_name}_{param_name}')

				# Determine if field is required and handle defaults
				if param_name in required:
					default = ...  # Required field
				else:
					# Optional field - make type optional and handle default
					param_type = param_type | None
					if 'default' in param_schema:
						default = param_schema['default']
					else:
						default = None

				# Add field with description if available
				field_kwargs = {}
				if 'description' in param_schema:
					field_kwargs['description'] = param_schema['description']

				param_fields[param_name] = (param_type, Field(default, **field_kwargs))

		# Create Pydantic model for the tool parameters
		if param_fields:
			# Create a BaseModel class with proper configuration
			class ConfiguredBaseModel(BaseModel):
				model_config = ConfigDict(extra='forbid', validate_by_name=True, validate_by_alias=True)

			param_model = create_model(f'{action_name}_Params', __base__=ConfiguredBaseModel, **param_fields)
		else:
			# No parameters - create empty model
			param_model = None

		# Determine if this is a browser-specific tool
		is_browser_tool = tool.name.startswith('browser_') or 'page' in tool.name.lower()

		# Set up action filters
		domains = None
		# Note: page_filter has been removed since we no longer use Page objects
		# Browser tools filtering would need to be done via domain filters instead

		# Create async wrapper function for the MCP tool
		# Need to define function with explicit parameters to satisfy registry validation
		if param_model:
			# Type 1: Function takes param model as first parameter
			async def mcp_action_wrapper(params: param_model) -> ActionResult:  # type: ignore[no-redef]
				"""Wrapper function that calls the MCP tool."""
				if not self.session or not self._connected:
					return ActionResult(error=f"MCP server '{self.server_name}' not connected", success=False)

				# Convert pydantic model to dict for MCP call
				tool_params = params.model_dump(exclude_none=True)

				logger.debug(f"🔧 Calling MCP tool '{tool.name}' with params: {tool_params}")

				start_time = time.time()
				error_msg = None

				try:
					# Call the MCP tool
					result = await self.session.call_tool(tool.name, tool_params)

					# Convert MCP result to ActionResult
					extracted_content = self._format_mcp_result(result)

					return ActionResult(
						extracted_content=extracted_content,
						long_term_memory=f"Used MCP tool '{tool.name}' from {self.server_name}",
						include_extracted_content_only_once=True,
					)

				except Exception as e:
					error_msg = f"MCP tool '{tool.name}' failed: {str(e)}"
					logger.error(error_msg)
					return ActionResult(error=error_msg, success=False)
				finally:
					# Capture telemetry for tool call
					duration = time.time() - start_time
					self._telemetry.capture(
						MCPClientTelemetryEvent(
							server_name=self.server_name,
							command=self.command,
							tools_discovered=len(self._tools),
							version=get_browser_use_version(),
							action='tool_call',
							tool_name=tool.name,
							duration_seconds=duration,
							error_message=error_msg,
						)
					)
		else:
			# No parameters - empty function signature
			async def mcp_action_wrapper() -> ActionResult:  # type: ignore[no-redef]
				"""Wrapper function that calls the MCP tool."""
				if not self.session or not self._connected:
					return ActionResult(error=f"MCP server '{self.server_name}' not connected", success=False)

				logger.debug(f"🔧 Calling MCP tool '{tool.name}' with no params")

				start_time = time.time()
				error_msg = None

				try:
					# Call the MCP tool with empty params
					result = await self.session.call_tool(tool.name, {})

					# Convert MCP result to ActionResult
					extracted_content = self._format_mcp_result(result)

					return ActionResult(
						extracted_content=extracted_content,
						long_term_memory=f"Used MCP tool '{tool.name}' from {self.server_name}",
						include_extracted_content_only_once=True,
					)

				except Exception as e:
					error_msg = f"MCP tool '{tool.name}' failed: {str(e)}"
					logger.error(error_msg)
					return ActionResult(error=error_msg, success=False)
				finally:
					# Capture telemetry for tool call
					duration = time.time() - start_time
					self._telemetry.capture(
						MCPClientTelemetryEvent(
							server_name=self.server_name,
							command=self.command,
							tools_discovered=len(self._tools),
							version=get_browser_use_version(),
							action='tool_call',
							tool_name=tool.name,
							duration_seconds=duration,
							error_message=error_msg,
						)
					)

		# Set function metadata for better debugging
		mcp_action_wrapper.__name__ = action_name
		mcp_action_wrapper.__qualname__ = f'mcp.{self.server_name}.{action_name}'

		# Register the action with browser-use
		description = tool.description or f'MCP tool from {self.server_name}: {tool.name}'

		# Use the registry's action decorator
		registry.action(description=description, param_model=param_model, domains=domains)(mcp_action_wrapper)

		logger.debug(f"✅ Registered MCP tool '{tool.name}' as action '{action_name}'")
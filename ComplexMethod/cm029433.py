def _register_tool_as_action(self, tool_name: str, tool: Tool):
		"""Register an MCP tool as a browser-use action.

		Args:
			tool_name: Name of the MCP tool
			tool: MCP Tool object with schema information
		"""
		if tool_name in self._registered_actions:
			return  # Already registered

		# Parse tool parameters to create Pydantic model
		param_fields = {}

		if tool.inputSchema:
			# MCP tools use JSON Schema for parameters
			properties = tool.inputSchema.get('properties', {})
			required = set(tool.inputSchema.get('required', []))

			for param_name, param_schema in properties.items():
				# Convert JSON Schema type to Python type
				param_type = self._json_schema_to_python_type(param_schema)

				# Determine if field is required
				if param_name in required:
					default = ...  # Required field
				else:
					default = param_schema.get('default', None)

				# Add field description if available
				field_kwargs = {}
				if 'description' in param_schema:
					field_kwargs['description'] = param_schema['description']

				param_fields[param_name] = (param_type, Field(default, **field_kwargs))

		# Create Pydantic model for the tool parameters
		param_model = create_model(f'{tool_name}_Params', **param_fields) if param_fields else None

		# Determine if this is a browser-specific tool
		is_browser_tool = tool_name.startswith('browser_')
		domains = None
		# Note: page_filter has been removed since we no longer use Page objects

		# Create wrapper function for the MCP tool
		async def mcp_action_wrapper(**kwargs):
			"""Wrapper function that calls the MCP tool."""
			if not self.session:
				raise RuntimeError(f'MCP session not connected for tool {tool_name}')

			# Extract parameters (excluding special injected params)
			special_params = {
				'page',
				'browser_session',
				'context',
				'page_extraction_llm',
				'file_system',
				'available_file_paths',
				'has_sensitive_data',
				'browser',
				'browser_context',
			}

			tool_params = {k: v for k, v in kwargs.items() if k not in special_params}

			logger.debug(f'🔧 Calling MCP tool {tool_name} with params: {tool_params}')

			try:
				# Call the MCP tool
				result = await self.session.call_tool(tool_name, tool_params)

				# Convert MCP result to ActionResult
				# MCP tools return results in various formats
				if hasattr(result, 'content'):
					# Handle structured content responses
					if isinstance(result.content, list):
						# Multiple content items
						content_parts = []
						for item in result.content:
							if isinstance(item, TextContent):
								content_parts.append(item.text)  # type: ignore[reportAttributeAccessIssue]
							else:
								content_parts.append(str(item))
						extracted_content = '\n'.join(content_parts)
					else:
						extracted_content = str(result.content)
				else:
					# Direct result
					extracted_content = str(result)

				return ActionResult(extracted_content=extracted_content)

			except Exception as e:
				logger.error(f'❌ MCP tool {tool_name} failed: {e}')
				return ActionResult(extracted_content=f'MCP tool {tool_name} failed: {str(e)}', error=str(e))

		# Set function name for better debugging
		mcp_action_wrapper.__name__ = tool_name
		mcp_action_wrapper.__qualname__ = f'mcp.{tool_name}'

		# Register the action with browser-use
		description = tool.description or f'MCP tool: {tool_name}'

		# Use the decorator to register the action
		decorated_wrapper = self.registry.action(description=description, param_model=param_model, domains=domains)(
			mcp_action_wrapper
		)

		self._registered_actions.add(tool_name)
		logger.info(f'✅ Registered MCP tool as action: {tool_name}')
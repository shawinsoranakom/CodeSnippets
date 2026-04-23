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
def _format_mcp_result(self, result: Any) -> str:
		"""Format MCP tool result into a string for ActionResult.

		Args:
			result: Raw result from MCP tool call

		Returns:
			Formatted string representation of the result
		"""
		# Handle different MCP result formats
		if hasattr(result, 'content'):
			# Structured content response
			if isinstance(result.content, list):
				# Multiple content items
				parts = []
				for item in result.content:
					if hasattr(item, 'text'):
						parts.append(item.text)
					elif hasattr(item, 'type') and item.type == 'text':
						parts.append(str(item))
					else:
						parts.append(str(item))
				return '\n'.join(parts)
			else:
				return str(result.content)
		elif isinstance(result, list):
			# List of content items
			parts = []
			for item in result:
				if hasattr(item, 'text'):
					parts.append(item.text)
				else:
					parts.append(str(item))
			return '\n'.join(parts)
		else:
			# Direct result or unknown format
			return str(result)
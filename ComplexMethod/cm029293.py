async def get_dom_element_at_coordinates(self, x: int, y: int) -> EnhancedDOMTreeNode | None:
		"""Get DOM element at coordinates as EnhancedDOMTreeNode.

		First checks the cached selector_map for a matching element, then falls back
		to CDP DOM.describeNode if not found. This ensures safety checks (e.g., for
		<select> elements and file inputs) work correctly.

		Args:
			x: X coordinate relative to viewport
			y: Y coordinate relative to viewport

		Returns:
			EnhancedDOMTreeNode at the coordinates, or None if no element found
		"""
		from browser_use.dom.views import NodeType

		# Get current page to access CDP session
		page = await self.get_current_page()
		if page is None:
			raise RuntimeError('No active page found')

		# Get session ID for CDP call
		session_id = await page._ensure_session()

		try:
			# Call CDP DOM.getNodeForLocation to get backend_node_id
			result = await self.cdp_client.send.DOM.getNodeForLocation(
				params={
					'x': x,
					'y': y,
					'includeUserAgentShadowDOM': False,
					'ignorePointerEventsNone': False,
				},
				session_id=session_id,
			)

			backend_node_id = result.get('backendNodeId')
			if backend_node_id is None:
				self.logger.debug(f'No element found at coordinates ({x}, {y})')
				return None

			# Try to find element in cached selector_map (avoids extra CDP call)
			if self._cached_selector_map:
				for node in self._cached_selector_map.values():
					if node.backend_node_id == backend_node_id:
						self.logger.debug(f'Found element at ({x}, {y}) in cached selector_map')
						return node

			# Not in cache - fall back to CDP DOM.describeNode to get actual node info
			try:
				describe_result = await self.cdp_client.send.DOM.describeNode(
					params={'backendNodeId': backend_node_id},
					session_id=session_id,
				)
				node_info = describe_result.get('node', {})
				node_name = node_info.get('nodeName', '')

				# Parse attributes from flat list [key1, val1, key2, val2, ...] to dict
				attrs_list = node_info.get('attributes', [])
				attributes = {attrs_list[i]: attrs_list[i + 1] for i in range(0, len(attrs_list), 2)}

				return EnhancedDOMTreeNode(
					node_id=result.get('nodeId', 0),
					backend_node_id=backend_node_id,
					node_type=NodeType(node_info.get('nodeType', NodeType.ELEMENT_NODE.value)),
					node_name=node_name,
					node_value=node_info.get('nodeValue', '') or '',
					attributes=attributes,
					is_scrollable=None,
					frame_id=result.get('frameId'),
					session_id=session_id,
					target_id=self.agent_focus_target_id or '',
					content_document=None,
					shadow_root_type=None,
					shadow_roots=None,
					parent_node=None,
					children_nodes=None,
					ax_node=None,
					snapshot_node=None,
					is_visible=None,
					absolute_position=None,
				)
			except Exception as e:
				self.logger.debug(f'DOM.describeNode failed for backend_node_id={backend_node_id}: {e}')
				# Fall back to minimal node if describeNode fails
				return EnhancedDOMTreeNode(
					node_id=result.get('nodeId', 0),
					backend_node_id=backend_node_id,
					node_type=NodeType.ELEMENT_NODE,
					node_name='',
					node_value='',
					attributes={},
					is_scrollable=None,
					frame_id=result.get('frameId'),
					session_id=session_id,
					target_id=self.agent_focus_target_id or '',
					content_document=None,
					shadow_root_type=None,
					shadow_roots=None,
					parent_node=None,
					children_nodes=None,
					ax_node=None,
					snapshot_node=None,
					is_visible=None,
					absolute_position=None,
				)

		except Exception as e:
			self.logger.warning(f'Failed to get DOM element at coordinates ({x}, {y}): {e}')
			return None
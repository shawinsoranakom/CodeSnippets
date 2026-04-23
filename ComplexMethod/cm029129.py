def _create_simplified_tree(self, node: EnhancedDOMTreeNode, depth: int = 0) -> SimplifiedNode | None:
		"""Step 1: Create a simplified tree with enhanced element detection."""

		if node.node_type == NodeType.DOCUMENT_NODE:
			# for all cldren including shadow roots
			for child in node.children_and_shadow_roots:
				simplified_child = self._create_simplified_tree(child, depth + 1)
				if simplified_child:
					return simplified_child

			return None

		if node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# ENHANCED shadow DOM processing - always include shadow content
			simplified = SimplifiedNode(original_node=node, children=[])
			for child in node.children_and_shadow_roots:
				simplified_child = self._create_simplified_tree(child, depth + 1)
				if simplified_child:
					simplified.children.append(simplified_child)

			# Always return shadow DOM fragments, even if children seem empty
			# Shadow DOM often contains the actual interactive content in SPAs
			return simplified if simplified.children else SimplifiedNode(original_node=node, children=[])

		elif node.node_type == NodeType.ELEMENT_NODE:
			# Skip non-content elements
			if node.node_name.lower() in DISABLED_ELEMENTS:
				return None

			# Skip SVG child elements entirely (path, rect, g, circle, etc.)
			if node.node_name.lower() in SVG_ELEMENTS:
				return None

			attributes = node.attributes or {}
			# Check for session-specific exclude attribute first, then fall back to legacy attribute
			exclude_attr = None
			attr_type = None
			if self.session_id:
				session_specific_attr = f'data-browser-use-exclude-{self.session_id}'
				exclude_attr = attributes.get(session_specific_attr)
				if exclude_attr:
					attr_type = 'session-specific'
			# Fall back to legacy attribute if session-specific not found
			if not exclude_attr:
				exclude_attr = attributes.get('data-browser-use-exclude')
			if isinstance(exclude_attr, str) and exclude_attr.lower() == 'true':
				return None

			if node.node_name == 'IFRAME' or node.node_name == 'FRAME':
				if node.content_document:
					simplified = SimplifiedNode(original_node=node, children=[])
					for child in node.content_document.children_nodes or []:
						simplified_child = self._create_simplified_tree(child, depth + 1)
						if simplified_child is not None:
							simplified.children.append(simplified_child)
					return simplified

			is_visible = node.is_visible
			is_scrollable = node.is_actually_scrollable
			has_shadow_content = bool(node.children_and_shadow_roots)

			# ENHANCED SHADOW DOM DETECTION: Include shadow hosts even if not visible
			is_shadow_host = any(child.node_type == NodeType.DOCUMENT_FRAGMENT_NODE for child in node.children_and_shadow_roots)

			# Override visibility for elements with validation attributes
			if not is_visible and node.attributes:
				has_validation_attrs = any(attr.startswith(('aria-', 'pseudo')) for attr in node.attributes.keys())
				if has_validation_attrs:
					is_visible = True  # Force visibility for validation elements

			# EXCEPTION: File inputs are often hidden with opacity:0 but are still functional
			# Bootstrap and other frameworks use this pattern with custom-styled file pickers
			is_file_input = (
				node.tag_name and node.tag_name.lower() == 'input' and node.attributes and node.attributes.get('type') == 'file'
			)
			if not is_visible and is_file_input:
				is_visible = True  # Force visibility for file inputs

			# Include if visible, scrollable, has children, or is shadow host
			if is_visible or is_scrollable or has_shadow_content or is_shadow_host:
				simplified = SimplifiedNode(original_node=node, children=[], is_shadow_host=is_shadow_host)

				# Process ALL children including shadow roots with enhanced logging
				for child in node.children_and_shadow_roots:
					simplified_child = self._create_simplified_tree(child, depth + 1)
					if simplified_child:
						simplified.children.append(simplified_child)

				# COMPOUND CONTROL PROCESSING: Add virtual components for compound controls
				self._add_compound_components(simplified, node)

				# SHADOW DOM SPECIAL CASE: Always include shadow hosts even if not visible
				# Many SPA frameworks (React, Vue) render content in shadow DOM
				if is_shadow_host and simplified.children:
					return simplified

				# Return if meaningful or has meaningful children
				if is_visible or is_scrollable or simplified.children:
					return simplified
		elif node.node_type == NodeType.TEXT_NODE:
			# Include meaningful text nodes
			is_visible = node.snapshot_node and node.is_visible
			if is_visible and node.node_value and node.node_value.strip() and len(node.node_value.strip()) > 1:
				return SimplifiedNode(original_node=node, children=[])

		return None
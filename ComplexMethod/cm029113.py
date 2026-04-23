def process_node(current_node: EnhancedDOMTreeNode) -> None:
			"""Process node and descendants, collecting hidden elements for iframes."""
			if (
				current_node.node_type == NodeType.ELEMENT_NODE
				and current_node.tag_name
				and current_node.tag_name.upper() in ('IFRAME', 'FRAME')
				and current_node.content_document
			):
				# Get viewport height from iframe's client rect
				viewport_height = 0.0
				if current_node.snapshot_node and current_node.snapshot_node.clientRects:
					viewport_height = current_node.snapshot_node.clientRects.height

				hidden = collect_hidden_elements(current_node.content_document, viewport_height)
				# Sort by pages and limit to avoid bloating context
				hidden.sort(key=lambda x: x['pages'])
				current_node.hidden_elements_info = hidden[:10]  # Limit to 10

				# Check for hidden non-interactive content when no interactive elements found
				if not hidden and has_any_hidden_content(current_node.content_document):
					current_node.has_hidden_content = True

			for child in current_node.children_nodes or []:
				process_node(child)

			if current_node.content_document:
				process_node(current_node.content_document)

			for shadow_root in current_node.shadow_roots or []:
				process_node(shadow_root)
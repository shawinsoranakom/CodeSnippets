def _serialize_document_node(
		dom_node: EnhancedDOMTreeNode,
		output: list[str],
		include_attributes: list[str],
		depth: int,
		is_iframe_content: bool = True,
	) -> None:
		"""Helper to serialize a document node without SimplifiedNode wrapper.

		Args:
			is_iframe_content: If True, be more permissive with visibility checks since
				iframe content might not have snapshot data from parent page.
		"""
		depth_str = depth * '\t'

		if dom_node.node_type == NodeType.ELEMENT_NODE:
			tag = dom_node.tag_name.lower()

			# For iframe content, be permissive - show all semantic elements even without snapshot data
			# For regular content, skip invisible elements
			if is_iframe_content:
				# Only skip if we have snapshot data AND it's explicitly invisible
				# If no snapshot data, assume visible (cross-origin iframe content)
				is_visible = (not dom_node.snapshot_node) or dom_node.is_visible
			else:
				# Regular strict visibility check
				is_visible = dom_node.snapshot_node and dom_node.is_visible

			if not is_visible:
				return

			# Check if semantic or has useful attributes
			is_semantic = tag in SEMANTIC_ELEMENTS
			attributes_str = DOMEvalSerializer._build_compact_attributes(dom_node)

			if not is_semantic and not attributes_str:
				# Skip but process children
				for child in dom_node.children:
					DOMEvalSerializer._serialize_document_node(
						child, output, include_attributes, depth, is_iframe_content=is_iframe_content
					)
				return

			# Build element line
			line = f'{depth_str}<{tag}'
			if attributes_str:
				line += f' {attributes_str}'

			# Get direct text content
			text_parts = []
			for child in dom_node.children:
				if child.node_type == NodeType.TEXT_NODE and child.node_value:
					text = child.node_value.strip()
					if text and len(text) > 1:
						text_parts.append(text)

			if text_parts:
				combined = ' '.join(text_parts)
				line += f'>{cap_text_length(combined, 100)}'
			else:
				line += ' />'

			output.append(line)

			# Process non-text children
			for child in dom_node.children:
				if child.node_type != NodeType.TEXT_NODE:
					DOMEvalSerializer._serialize_document_node(
						child, output, include_attributes, depth + 1, is_iframe_content=is_iframe_content
					)
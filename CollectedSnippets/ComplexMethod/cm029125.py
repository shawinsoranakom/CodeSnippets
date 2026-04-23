def serialize(self, node: EnhancedDOMTreeNode, depth: int = 0) -> str:
		"""Serialize an enhanced DOM tree node to HTML.

		Args:
			node: The enhanced DOM tree node to serialize
			depth: Current depth for indentation (internal use)

		Returns:
			HTML string representation of the node and its descendants
		"""
		if node.node_type == NodeType.DOCUMENT_NODE:
			# Process document root - serialize all children
			parts = []
			for child in node.children_and_shadow_roots:
				child_html = self.serialize(child, depth)
				if child_html:
					parts.append(child_html)
			return ''.join(parts)

		elif node.node_type == NodeType.DOCUMENT_FRAGMENT_NODE:
			# Shadow DOM root - wrap in template with shadowrootmode attribute
			parts = []

			# Add shadow root opening
			shadow_type = node.shadow_root_type or 'open'
			parts.append(f'<template shadowroot="{shadow_type.lower()}">')

			# Serialize shadow children
			for child in node.children:
				child_html = self.serialize(child, depth + 1)
				if child_html:
					parts.append(child_html)

			# Close shadow root
			parts.append('</template>')

			return ''.join(parts)

		elif node.node_type == NodeType.ELEMENT_NODE:
			parts = []
			tag_name = node.tag_name.lower()

			# Skip non-content elements
			if tag_name in {'style', 'script', 'head', 'meta', 'link', 'title'}:
				return ''

			# Skip code tags with display:none - these often contain JSON state for SPAs
			if tag_name == 'code' and node.attributes:
				style = node.attributes.get('style', '')
				# Check if element is hidden (display:none) - likely JSON data
				if 'display:none' in style.replace(' ', '') or 'display: none' in style:
					return ''
				# Also check for bpr-guid IDs (LinkedIn's JSON data pattern)
				element_id = node.attributes.get('id', '')
				if 'bpr-guid' in element_id or 'data' in element_id or 'state' in element_id:
					return ''

			# Skip base64 inline images - these are usually placeholders or tracking pixels
			if tag_name == 'img' and node.attributes:
				src = node.attributes.get('src', '')
				if src.startswith('data:image/'):
					return ''

			# Opening tag
			parts.append(f'<{tag_name}')

			# Add attributes
			if node.attributes:
				attrs = self._serialize_attributes(node.attributes)
				if attrs:
					parts.append(' ' + attrs)

			# Handle void elements (self-closing)
			void_elements = {
				'area',
				'base',
				'br',
				'col',
				'embed',
				'hr',
				'img',
				'input',
				'link',
				'meta',
				'param',
				'source',
				'track',
				'wbr',
			}
			if tag_name in void_elements:
				parts.append(' />')
				return ''.join(parts)

			parts.append('>')

			# Handle table normalization (ensure thead/tbody for markdownify)
			if tag_name == 'table':
				# Serialize shadow roots first (same as the general path)
				if node.shadow_roots:
					for shadow_root in node.shadow_roots:
						child_html = self.serialize(shadow_root, depth + 1)
						if child_html:
							parts.append(child_html)
				table_html = self._serialize_table_children(node, depth)
				parts.append(table_html)
			# Handle iframe content document
			elif tag_name in {'iframe', 'frame'} and node.content_document:
				# Serialize iframe content
				for child in node.content_document.children_nodes or []:
					child_html = self.serialize(child, depth + 1)
					if child_html:
						parts.append(child_html)
			else:
				# Serialize shadow roots FIRST (for declarative shadow DOM)
				if node.shadow_roots:
					for shadow_root in node.shadow_roots:
						child_html = self.serialize(shadow_root, depth + 1)
						if child_html:
							parts.append(child_html)

				# Then serialize light DOM children (for slot projection)
				for child in node.children:
					child_html = self.serialize(child, depth + 1)
					if child_html:
						parts.append(child_html)

			# Closing tag
			parts.append(f'</{tag_name}>')

			return ''.join(parts)

		elif node.node_type == NodeType.TEXT_NODE:
			# Return text content with basic HTML escaping
			if node.node_value:
				return self._escape_html(node.node_value)
			return ''

		elif node.node_type == NodeType.COMMENT_NODE:
			# Skip comments to reduce noise
			return ''

		else:
			# Unknown node type - skip
			return ''
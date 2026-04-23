def _serialize_table_children(self, table_node: EnhancedDOMTreeNode, depth: int) -> str:
		"""Normalize table structure to ensure thead/tbody for markdownify.

		When a <table> has no <thead> but the first <tr> contains <th> cells,
		wrap that row in <thead> and remaining rows in <tbody>.
		"""
		children = table_node.children
		if not children:
			return ''

		# Check if table already has thead
		child_tags = [c.tag_name for c in children if c.node_type == NodeType.ELEMENT_NODE]
		has_thead = 'thead' in child_tags
		has_tbody = 'tbody' in child_tags

		if has_thead or not child_tags:
			# Already normalized or empty — serialize normally
			parts = []
			for child in children:
				child_html = self.serialize(child, depth + 1)
				if child_html:
					parts.append(child_html)
			return ''.join(parts)

		# Find the first <tr> with <th> cells
		first_tr = None
		first_tr_idx = -1
		for i, child in enumerate(children):
			if child.node_type == NodeType.ELEMENT_NODE and child.tag_name == 'tr':
				# Check if this row contains <th> cells
				has_th = any(c.node_type == NodeType.ELEMENT_NODE and c.tag_name == 'th' for c in child.children)
				if has_th:
					first_tr = child
					first_tr_idx = i
				break  # Only check the first <tr>

		if first_tr is None:
			# No header row detected — serialize normally
			parts = []
			for child in children:
				child_html = self.serialize(child, depth + 1)
				if child_html:
					parts.append(child_html)
			return ''.join(parts)

		# Wrap first_tr in <thead>, remaining <tr> in <tbody>
		parts = []

		# Emit any children before the header row (e.g. colgroup, caption)
		for child in children[:first_tr_idx]:
			child_html = self.serialize(child, depth + 1)
			if child_html:
				parts.append(child_html)

		# Emit <thead>
		parts.append('<thead>')
		parts.append(self.serialize(first_tr, depth + 2))
		parts.append('</thead>')

		# Collect remaining rows
		remaining = children[first_tr_idx + 1 :]
		if remaining and not has_tbody:
			parts.append('<tbody>')
			for child in remaining:
				child_html = self.serialize(child, depth + 2)
				if child_html:
					parts.append(child_html)
			parts.append('</tbody>')
		else:
			for child in remaining:
				child_html = self.serialize(child, depth + 1)
				if child_html:
					parts.append(child_html)

		return ''.join(parts)
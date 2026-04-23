def __json__(self) -> dict:
		"""Serializes the node and its descendants to a dictionary, omitting parent references."""
		return {
			'node_id': self.node_id,
			'backend_node_id': self.backend_node_id,
			'node_type': self.node_type.name,
			'node_name': self.node_name,
			'node_value': self.node_value,
			'is_visible': self.is_visible,
			'attributes': self.attributes,
			'is_scrollable': self.is_scrollable,
			'session_id': self.session_id,
			'target_id': self.target_id,
			'frame_id': self.frame_id,
			'content_document': self.content_document.__json__() if self.content_document else None,
			'shadow_root_type': self.shadow_root_type,
			'ax_node': asdict(self.ax_node) if self.ax_node else None,
			'snapshot_node': asdict(self.snapshot_node) if self.snapshot_node else None,
			# these two in the end, so it's easier to read json
			'shadow_roots': [r.__json__() for r in self.shadow_roots] if self.shadow_roots else [],
			'children_nodes': [c.__json__() for c in self.children_nodes] if self.children_nodes else [],
		}
def compute_stable_hash(self) -> int:
		"""
		Compute hash with dynamic classes filtered out.
		More stable across sessions than element_hash since it excludes
		transient CSS state classes like focus, hover, animation, etc.
		"""
		parent_branch_path = self._get_parent_branch_path()
		parent_branch_path_string = '/'.join(parent_branch_path)

		# Filter dynamic classes before building attributes string
		filtered_attrs: dict[str, str] = {}
		for k, v in self.attributes.items():
			if k not in STATIC_ATTRIBUTES:
				continue
			if k == 'class':
				v = filter_dynamic_classes(v)
				if not v:  # Skip empty class after filtering
					continue
			filtered_attrs[k] = v

		attributes_string = ''.join(f'{k}={v}' for k, v in sorted(filtered_attrs.items()))

		ax_name = ''
		if self.ax_node and self.ax_node.name:
			ax_name = f'|ax_name={self.ax_node.name}'

		combined_string = f'{parent_branch_path_string}|{attributes_string}{ax_name}'
		hash_hex = hashlib.sha256(combined_string.encode()).hexdigest()
		return int(hash_hex[:16], 16)
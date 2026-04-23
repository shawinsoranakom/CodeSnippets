def should_show_scroll_info(self) -> bool:
		"""
		Simple check: show scroll info only if this element is scrollable
		and doesn't have a scrollable parent (to avoid nested scroll spam).

		Special case for iframes: Always show scroll info since Chrome might not
		always detect iframe scrollability correctly (scrollHeight: 0 issue).
		"""
		# Special case: Always show scroll info for iframe elements
		# Even if not detected as scrollable, they might have scrollable content
		if self.tag_name.lower() == 'iframe':
			return True

		# Must be scrollable first for non-iframe elements
		if not (self.is_scrollable or self.is_actually_scrollable):
			return False

		# Always show for iframe content documents (body/html)
		if self.tag_name.lower() in {'body', 'html'}:
			return True

		# Don't show if parent is already scrollable (avoid nested spam)
		if self.parent_node and (self.parent_node.is_scrollable or self.parent_node.is_actually_scrollable):
			return False

		return True
def _is_menu_opener_step(self, history_item: AgentHistory | None) -> bool:
		"""
		Detect if a step opens a dropdown/menu.

		Checks for common patterns indicating a menu opener:
		- Element has aria-haspopup attribute
		- Element has data-gw-click="toggleSubMenu" (Guidewire pattern)
		- Element has expand-button in class name
		- Element role is "menuitem" with aria-expanded

		Returns True if the step appears to open a dropdown/submenu.
		"""
		if not history_item or not history_item.state or not history_item.state.interacted_element:
			return False

		elem = history_item.state.interacted_element[0] if history_item.state.interacted_element else None
		if not elem:
			return False

		attrs = elem.attributes or {}

		# Check for common menu opener indicators
		if attrs.get('aria-haspopup') in ('true', 'menu', 'listbox'):
			return True
		if attrs.get('data-gw-click') == 'toggleSubMenu':
			return True
		if 'expand-button' in attrs.get('class', ''):
			return True
		if attrs.get('role') == 'menuitem' and attrs.get('aria-expanded') in ('false', 'true'):
			return True
		if attrs.get('role') == 'button' and attrs.get('aria-expanded') in ('false', 'true'):
			return True

		return False
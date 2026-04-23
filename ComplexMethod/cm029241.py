def _is_menu_item_element(self, elem: 'DOMInteractedElement | None') -> bool:
		"""
		Detect if an element is a menu item that appears inside a dropdown/menu.

		Checks for:
		- role="menuitem", "option", "menuitemcheckbox", "menuitemradio"
		- Element is inside a menu structure (has menu-related parent indicators)
		- ax_name is set (menu items typically have accessible names)

		Returns True if the element appears to be a menu item.
		"""
		if not elem:
			return False

		attrs = elem.attributes or {}

		# Check for menu item roles
		role = attrs.get('role', '')
		if role in ('menuitem', 'option', 'menuitemcheckbox', 'menuitemradio', 'treeitem'):
			return True

		# Elements in Guidewire menus have these patterns
		if 'gw-action--inner' in attrs.get('class', ''):
			return True
		if 'menuitem' in attrs.get('class', '').lower():
			return True

		# If element has an ax_name and looks like it could be in a menu
		# This is a softer check - only used if the previous step was a menu opener
		if elem.ax_name and elem.ax_name not in ('', None):
			# Common menu container classes
			elem_class = attrs.get('class', '').lower()
			if any(x in elem_class for x in ['dropdown', 'popup', 'menu', 'submenu', 'action']):
				return True

		return False
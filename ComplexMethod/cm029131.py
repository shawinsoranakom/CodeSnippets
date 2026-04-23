def _assign_interactive_indices_and_mark_new_nodes(self, node: SimplifiedNode | None) -> None:
		"""Assign interactive indices to clickable elements that are also visible."""
		if not node:
			return

		# Skip assigning index to excluded nodes, or ignored by paint order
		if not node.excluded_by_parent and not node.ignored_by_paint_order:
			# Regular interactive element assignment (including enhanced compound controls)
			is_interactive_assign = self._is_interactive_cached(node.original_node)
			is_visible = node.original_node.snapshot_node and node.original_node.is_visible
			is_scrollable = node.original_node.is_actually_scrollable

			# DIAGNOSTIC: Log when interactive elements don't have snapshot_node
			if is_interactive_assign and not node.original_node.snapshot_node:
				import logging

				logger = logging.getLogger('browser_use.dom.serializer')
				attrs = node.original_node.attributes or {}
				attr_str = f'name={attrs.get("name", "")} id={attrs.get("id", "")} type={attrs.get("type", "")}'
				in_shadow = self._is_inside_shadow_dom(node)
				if (
					in_shadow
					and node.original_node.tag_name
					and node.original_node.tag_name.lower() in ['input', 'button', 'select', 'textarea', 'a']
				):
					logger.debug(
						f'🔍 INCLUDING shadow DOM <{node.original_node.tag_name}> (no snapshot_node but in shadow DOM): '
						f'backendNodeId={node.original_node.backend_node_id} {attr_str}'
					)
				else:
					logger.debug(
						f'🔍 SKIPPING interactive <{node.original_node.tag_name}> (no snapshot_node, not in shadow DOM): '
						f'backendNodeId={node.original_node.backend_node_id} {attr_str}'
					)

			# EXCEPTION: File inputs are often hidden with opacity:0 but are still functional
			# Bootstrap and other frameworks use this pattern with custom-styled file pickers
			is_file_input = (
				node.original_node.tag_name
				and node.original_node.tag_name.lower() == 'input'
				and node.original_node.attributes
				and node.original_node.attributes.get('type') == 'file'
			)

			# EXCEPTION: Shadow DOM form elements may not have snapshot layout data from CDP's
			# DOMSnapshot.captureSnapshot, but they're still functional/interactive.
			# This handles login forms, custom web components, etc. inside shadow DOM.
			is_shadow_dom_element = (
				is_interactive_assign
				and not node.original_node.snapshot_node
				and node.original_node.tag_name
				and node.original_node.tag_name.lower() in ['input', 'button', 'select', 'textarea', 'a']
				and self._is_inside_shadow_dom(node)
			)

			# Check if scrollable container should be made interactive
			# For scrollable elements, ONLY make them interactive if they have no interactive descendants
			should_make_interactive = False
			if is_scrollable:
				# Check if this is a dropdown container that needs to be indexed regardless of descendants
				attrs = node.original_node.attributes or {}
				role = attrs.get('role', '').lower()
				tag_name = (node.original_node.tag_name or '').lower()
				class_attr = attrs.get('class', '').lower()
				class_list = class_attr.split() if class_attr else []

				# Detect dropdown containers by role, tag, or class
				is_dropdown_by_role = role in ('listbox', 'menu', 'combobox', 'menubar', 'tree', 'grid')
				is_dropdown_by_tag = tag_name == 'select'
				# Match common dropdown class patterns
				is_dropdown_by_class = (
					'dropdown' in class_list
					or 'dropdown-menu' in class_list
					or 'select-menu' in class_list
					or ('ui' in class_list and 'dropdown' in class_attr)  # Semantic UI
				)
				is_dropdown_container = is_dropdown_by_role or is_dropdown_by_tag or is_dropdown_by_class

				if is_dropdown_container:
					# Always index dropdown containers - need to be targetable for select_dropdown
					should_make_interactive = True
				else:
					# For other scrollable elements, check if they have interactive children
					has_interactive_desc = self._has_interactive_descendants(node)
					# Only make scrollable container interactive if it has no interactive descendants
					if not has_interactive_desc:
						should_make_interactive = True
			elif is_interactive_assign and (is_visible or is_file_input or is_shadow_dom_element):
				# Non-scrollable interactive elements: make interactive if visible (or file input or shadow DOM form element)
				should_make_interactive = True

			# Add to selector map if element should be interactive
			if should_make_interactive:
				# Mark node as interactive
				node.is_interactive = True
				# Store backend_node_id in selector map (model outputs backend_node_id)
				self._selector_map[node.original_node.backend_node_id] = node.original_node
				self._interactive_counter += 1

				# Mark compound components as new for visibility
				if node.is_compound_component:
					node.is_new = True
				elif self._previous_cached_selector_map:
					# Check if node is new for regular elements
					previous_backend_node_ids = {node.backend_node_id for node in self._previous_cached_selector_map.values()}
					if node.original_node.backend_node_id not in previous_backend_node_ids:
						node.is_new = True

		# Process children
		for child in node.children:
			self._assign_interactive_indices_and_mark_new_nodes(child)
async def _update_action_indices(
		self,
		historical_element: DOMInteractedElement | None,
		action: ActionModel,  # Type this properly based on your action model
		browser_state_summary: BrowserStateSummary,
	) -> ActionModel | None:
		"""
		Update action indices based on current page state.
		Returns updated action or None if element cannot be found.

		Cascading matching strategy (tries each level in order):
		1. EXACT: Full element_hash match (includes all attributes + ax_name)
		2. STABLE: Hash with dynamic CSS classes filtered out (focus, hover, animation, etc.)
		3. XPATH: XPath string match (structural position in DOM)
		4. AX_NAME: Accessible name match from accessibility tree (robust for dynamic menus)
		5. ATTRIBUTE: Unique attribute match (name, id, aria-label) for old history files
		"""
		if not historical_element or not browser_state_summary.dom_state.selector_map:
			return action

		selector_map = browser_state_summary.dom_state.selector_map
		highlight_index: int | None = None
		match_level: MatchLevel | None = None

		# Debug: log what we're looking for and what's available
		self.logger.info(
			f'🔍 Searching for element: <{historical_element.node_name}> '
			f'hash={historical_element.element_hash} stable_hash={historical_element.stable_hash}'
		)
		# Log what elements are in selector_map for debugging
		if historical_element.node_name:
			hist_name = historical_element.node_name.lower()
			matching_nodes = [
				(idx, elem.node_name, elem.attributes.get('name') if elem.attributes else None)
				for idx, elem in selector_map.items()
				if elem.node_name.lower() == hist_name
			]
			self.logger.info(
				f'🔍 Selector map has {len(selector_map)} elements, '
				f'{len(matching_nodes)} are <{hist_name.upper()}>: {matching_nodes}'
			)

		# Level 1: EXACT hash match
		for idx, elem in selector_map.items():
			if elem.element_hash == historical_element.element_hash:
				highlight_index = idx
				match_level = MatchLevel.EXACT
				break

		if highlight_index is None:
			self.logger.debug(f'EXACT hash match failed (checked {len(selector_map)} elements)')

		# Level 2: STABLE hash match (dynamic classes filtered)
		# Use stored stable_hash (computed at save time from EnhancedDOMTreeNode - single source of truth)
		if highlight_index is None and historical_element.stable_hash is not None:
			for idx, elem in selector_map.items():
				if elem.compute_stable_hash() == historical_element.stable_hash:
					highlight_index = idx
					match_level = MatchLevel.STABLE
					self.logger.info('Element matched at STABLE level (dynamic classes filtered)')
					break
			if highlight_index is None:
				self.logger.debug('STABLE hash match failed')
		elif highlight_index is None:
			self.logger.debug('STABLE hash match skipped (no stable_hash in history)')

		# Level 3: XPATH match
		if highlight_index is None and historical_element.x_path:
			for idx, elem in selector_map.items():
				if elem.xpath == historical_element.x_path:
					highlight_index = idx
					match_level = MatchLevel.XPATH
					self.logger.info(f'Element matched at XPATH level: {historical_element.x_path}')
					break
			if highlight_index is None:
				self.logger.debug(f'XPATH match failed for: {historical_element.x_path[-60:]}')

		# Level 4: ax_name (accessible name) match - robust for dynamic SPAs with menus
		# This uses the accessible name from the accessibility tree which is stable
		# even when DOM structure changes (e.g., dynamically generated menu items)
		if highlight_index is None and historical_element.ax_name:
			hist_name = historical_element.node_name.lower()
			hist_ax_name = historical_element.ax_name
			for idx, elem in selector_map.items():
				# Match by node type and accessible name
				elem_ax_name = elem.ax_node.name if elem.ax_node else None
				if elem.node_name.lower() == hist_name and elem_ax_name == hist_ax_name:
					highlight_index = idx
					match_level = MatchLevel.AX_NAME
					self.logger.info(f'Element matched at AX_NAME level: "{hist_ax_name}"')
					break
			if highlight_index is None:
				# Log available ax_names for debugging
				same_type_ax_names = [
					(idx, elem.ax_node.name if elem.ax_node else None)
					for idx, elem in selector_map.items()
					if elem.node_name.lower() == hist_name and elem.ax_node and elem.ax_node.name
				]
				self.logger.debug(
					f'AX_NAME match failed for <{hist_name.upper()}> ax_name="{hist_ax_name}". '
					f'Page has {len(same_type_ax_names)} <{hist_name.upper()}> with ax_names: '
					f'{same_type_ax_names[:5]}{"..." if len(same_type_ax_names) > 5 else ""}'
				)

		# Level 5: Unique attribute fallback (for old history files without stable_hash)
		if highlight_index is None and historical_element.attributes:
			hist_attrs = historical_element.attributes
			hist_name = historical_element.node_name.lower()

			# Try matching by unique identifiers: name, id, or aria-label
			for attr_key in ['name', 'id', 'aria-label']:
				if attr_key in hist_attrs and hist_attrs[attr_key]:
					for idx, elem in selector_map.items():
						if (
							elem.node_name.lower() == hist_name
							and elem.attributes
							and elem.attributes.get(attr_key) == hist_attrs[attr_key]
						):
							highlight_index = idx
							match_level = MatchLevel.ATTRIBUTE
							self.logger.info(f'Element matched via {attr_key} attribute: {hist_attrs[attr_key]}')
							break
					if highlight_index is not None:
						break

			if highlight_index is None:
				tried_attrs = [k for k in ['name', 'id', 'aria-label'] if k in hist_attrs and hist_attrs[k]]
				# Log what was tried and what's available on the page for debugging
				same_node_elements = [
					(idx, elem.attributes.get('aria-label') or elem.attributes.get('id') or elem.attributes.get('name'))
					for idx, elem in selector_map.items()
					if elem.node_name.lower() == hist_name and elem.attributes
				]
				self.logger.info(
					f'🔍 ATTRIBUTE match failed for <{hist_name.upper()}> '
					f'(tried: {tried_attrs}, looking for: {[hist_attrs.get(k) for k in tried_attrs]}). '
					f'Page has {len(same_node_elements)} <{hist_name.upper()}> elements with identifiers: '
					f'{same_node_elements[:5]}{"..." if len(same_node_elements) > 5 else ""}'
				)

		if highlight_index is None:
			return None

		old_index = action.get_index()
		if old_index != highlight_index:
			action.set_index(highlight_index)
			level_name = match_level.name if match_level else 'UNKNOWN'
			self.logger.info(f'Element index updated {old_index} → {highlight_index} (matched at {level_name} level)')

		return action
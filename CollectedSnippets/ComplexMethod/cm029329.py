async def on_GetDropdownOptionsEvent(self, event: GetDropdownOptionsEvent) -> dict[str, str]:
		"""Handle get dropdown options request with CDP."""
		try:
			# Use the provided node
			element_node = event.node
			index_for_logging = element_node.backend_node_id or 'unknown'

			# Get CDP session for this node
			cdp_session = await self.browser_session.cdp_client_for_node(element_node)

			# Convert node to object ID for CDP operations
			try:
				object_result = await cdp_session.cdp_client.send.DOM.resolveNode(
					params={'backendNodeId': element_node.backend_node_id}, session_id=cdp_session.session_id
				)
				remote_object = object_result.get('object', {})
				object_id = remote_object.get('objectId')
				if not object_id:
					raise ValueError('Could not get object ID from resolved node')
			except Exception as e:
				raise ValueError(f'Failed to resolve node to object: {e}') from e

			# Check if this is an ARIA combobox that needs expansion
			# ARIA comboboxes have options in a separate element referenced by aria-controls
			check_combobox_script = """
			function() {
				const element = this;
				const role = element.getAttribute('role');
				const ariaControls = element.getAttribute('aria-controls');
				const ariaExpanded = element.getAttribute('aria-expanded');

				if (role === 'combobox' && ariaControls) {
					return {
						isCombobox: true,
						ariaControls: ariaControls,
						isExpanded: ariaExpanded === 'true',
						tagName: element.tagName.toLowerCase()
					};
				}
				return { isCombobox: false };
			}
			"""

			combobox_check = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': check_combobox_script,
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)
			combobox_info = combobox_check.get('result', {}).get('value', {})

			# If it's an ARIA combobox with aria-controls, handle it specially
			if combobox_info.get('isCombobox'):
				return await self._handle_aria_combobox_options(cdp_session, object_id, combobox_info, index_for_logging)

			# Use JavaScript to extract dropdown options (existing logic for non-combobox elements)
			options_script = """
			function() {
				const startElement = this;

				// Function to check if an element is a dropdown and extract options
				function checkDropdownElement(element) {
					// Check if it's a native select element
					if (element.tagName.toLowerCase() === 'select') {
						return {
							type: 'select',
							options: Array.from(element.options).map((opt, idx) => ({
								text: opt.text.trim(),
								value: opt.value,
								index: idx,
								selected: opt.selected
							})),
							id: element.id || '',
							name: element.name || '',
							source: 'target'
						};
					}

					// Check if it's an ARIA dropdown/menu (not combobox - handled separately)
					const role = element.getAttribute('role');
					if (role === 'menu' || role === 'listbox') {
						// Find all menu items/options
						const menuItems = element.querySelectorAll('[role="menuitem"], [role="option"]');
						const options = [];

						menuItems.forEach((item, idx) => {
							const text = item.textContent ? item.textContent.trim() : '';
							if (text) {
								options.push({
									text: text,
									value: item.getAttribute('data-value') || text,
									index: idx,
									selected: item.getAttribute('aria-selected') === 'true' || item.classList.contains('selected')
								});
							}
						});

						return {
							type: 'aria',
							options: options,
							id: element.id || '',
							name: element.getAttribute('aria-label') || '',
							source: 'target'
						};
					}

					// Check if it's a Semantic UI dropdown or similar
					if (element.classList.contains('dropdown') || element.classList.contains('ui')) {
						const menuItems = element.querySelectorAll('.item, .option, [data-value]');
						const options = [];

						menuItems.forEach((item, idx) => {
							const text = item.textContent ? item.textContent.trim() : '';
							if (text) {
								options.push({
									text: text,
									value: item.getAttribute('data-value') || text,
									index: idx,
									selected: item.classList.contains('selected') || item.classList.contains('active')
								});
							}
						});

						if (options.length > 0) {
							return {
								type: 'custom',
								options: options,
								id: element.id || '',
								name: element.getAttribute('aria-label') || '',
								source: 'target'
							};
						}
					}

					return null;
				}

				// Function to recursively search children up to specified depth
				function searchChildrenForDropdowns(element, maxDepth, currentDepth = 0) {
					if (currentDepth >= maxDepth) return null;

					// Check all direct children
					for (let child of element.children) {
						// Check if this child is a dropdown
						const result = checkDropdownElement(child);
						if (result) {
							result.source = `child-depth-${currentDepth + 1}`;
							return result;
						}

						// Recursively check this child's children
						const childResult = searchChildrenForDropdowns(child, maxDepth, currentDepth + 1);
						if (childResult) {
							return childResult;
						}
					}

					return null;
				}

				// First check the target element itself
				let dropdownResult = checkDropdownElement(startElement);
				if (dropdownResult) {
					return dropdownResult;
				}

				// If target element is not a dropdown, search children up to depth 4
				dropdownResult = searchChildrenForDropdowns(startElement, 4);
				if (dropdownResult) {
					return dropdownResult;
				}

				return {
					error: `Element and its children (depth 4) are not recognizable dropdown types (tag: ${startElement.tagName}, role: ${startElement.getAttribute('role')}, classes: ${startElement.className})`
				};
			}
			"""

			result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
				params={
					'functionDeclaration': options_script,
					'objectId': object_id,
					'returnByValue': True,
				},
				session_id=cdp_session.session_id,
			)

			dropdown_data = result.get('result', {}).get('value', {})

			if dropdown_data.get('error'):
				raise BrowserError(message=dropdown_data['error'], long_term_memory=dropdown_data['error'])

			if not dropdown_data.get('options'):
				msg = f'No options found in dropdown at index {index_for_logging}'
				return {
					'error': msg,
					'short_term_memory': msg,
					'long_term_memory': msg,
					'backend_node_id': str(index_for_logging),
				}

			# Format options for display
			formatted_options = []
			for opt in dropdown_data['options']:
				# Use JSON encoding to ensure exact string matching
				encoded_text = json.dumps(opt['text'])
				status = ' (selected)' if opt.get('selected') else ''
				formatted_options.append(f'{opt["index"]}: text={encoded_text}, value={json.dumps(opt["value"])}{status}')

			dropdown_type = dropdown_data.get('type', 'select')
			element_info = f'Index: {index_for_logging}, Type: {dropdown_type}, ID: {dropdown_data.get("id", "none")}, Name: {dropdown_data.get("name", "none")}'
			source_info = dropdown_data.get('source', 'unknown')

			if source_info == 'target':
				msg = f'Found {dropdown_type} dropdown ({element_info}):\n' + '\n'.join(formatted_options)
			else:
				msg = f'Found {dropdown_type} dropdown in {source_info} ({element_info}):\n' + '\n'.join(formatted_options)
			msg += (
				f'\n\nUse the exact text or value string (without quotes) in select_dropdown(index={index_for_logging}, text=...)'
			)

			if source_info == 'target':
				self.logger.info(f'📋 Found {len(dropdown_data["options"])} dropdown options for index {index_for_logging}')
			else:
				self.logger.info(
					f'📋 Found {len(dropdown_data["options"])} dropdown options for index {index_for_logging} in {source_info}'
				)

			# Create structured memory for the response
			short_term_memory = msg
			long_term_memory = f'Got dropdown options for index {index_for_logging}'

			# Return the dropdown data as a dict with structured memory
			return {
				'type': dropdown_type,
				'options': json.dumps(dropdown_data['options']),  # Convert list to JSON string for dict[str, str] type
				'element_info': element_info,
				'source': source_info,
				'formatted_options': '\n'.join(formatted_options),
				'message': msg,
				'short_term_memory': short_term_memory,
				'long_term_memory': long_term_memory,
				'backend_node_id': str(index_for_logging),
			}

		except BrowserError:
			# Re-raise BrowserError as-is to preserve structured memory
			raise
		except TimeoutError:
			msg = f'Failed to get dropdown options for index {index_for_logging} due to timeout.'
			self.logger.error(msg)
			raise BrowserError(message=msg, long_term_memory=msg)
		except Exception as e:
			msg = 'Failed to get dropdown options'
			error_msg = f'{msg}: {str(e)}'
			self.logger.error(error_msg)
			raise BrowserError(
				message=error_msg, long_term_memory=f'Failed to get dropdown options for index {index_for_logging}.'
			)
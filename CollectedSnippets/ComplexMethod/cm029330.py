async def on_SelectDropdownOptionEvent(self, event: SelectDropdownOptionEvent) -> dict[str, str]:
		"""Handle select dropdown option request with CDP."""
		try:
			# Use the provided node
			element_node = event.node
			index_for_logging = element_node.backend_node_id or 'unknown'
			target_text = event.text

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

			try:
				# Use JavaScript to select the option
				selection_script = """
				function(targetText) {
					const startElement = this;

					// Function to attempt selection on a dropdown element
					function attemptSelection(element) {
						// Handle native select elements
						if (element.tagName.toLowerCase() === 'select') {
							const options = Array.from(element.options);
							const targetTextLower = targetText.toLowerCase();

							for (const option of options) {
								const optionTextLower = option.text.trim().toLowerCase();
								const optionValueLower = option.value.toLowerCase();

								// Match against both text and value (case-insensitive)
								if (optionTextLower === targetTextLower || optionValueLower === targetTextLower) {
									const expectedValue = option.value;

									// Focus the element FIRST (important for Svelte/Vue/React and other reactive frameworks)
									// This simulates the user focusing on the dropdown before changing it
									element.focus();

									// Then set the value using multiple methods for maximum compatibility
									element.value = expectedValue;
									option.selected = true;
									element.selectedIndex = option.index;

									// Trigger all necessary events for reactive frameworks
									// 1. input event - critical for Vue's v-model and Svelte's bind:value
									const inputEvent = new Event('input', { bubbles: true, cancelable: true });
									element.dispatchEvent(inputEvent);

									// 2. change event - traditional form validation and framework reactivity
									const changeEvent = new Event('change', { bubbles: true, cancelable: true });
									element.dispatchEvent(changeEvent);

									// 3. blur event - completes the interaction, triggers validation
									element.blur();

									// Verification: Check if the selection actually stuck (avoid intercepting and resetting the value)
									if (element.value !== expectedValue) {
										// Selection was reverted - need to try clicking instead
										return {
											success: false,
											error: `Selection was set but reverted by page framework. The dropdown may require clicking.`,
											selectionReverted: true,
											targetOption: {
												text: option.text.trim(),
												value: expectedValue,
												index: option.index
											},
											availableOptions: Array.from(element.options).map(opt => ({
												text: opt.text.trim(),
												value: opt.value
											}))
										};
									}

									return {
										success: true,
										message: `Selected option: ${option.text.trim()} (value: ${option.value})`,
										value: option.value
									};
								}
							}

							// Return available options as separate field
							const availableOptions = options.map(opt => ({
								text: opt.text.trim(),
								value: opt.value
							}));

							return {
								success: false,
								error: `Option with text or value '${targetText}' not found in select element`,
								availableOptions: availableOptions
							};
						}

						// Handle ARIA dropdowns/menus
						const role = element.getAttribute('role');
						if (role === 'menu' || role === 'listbox' || role === 'combobox') {
							const menuItems = element.querySelectorAll('[role="menuitem"], [role="option"]');
							const targetTextLower = targetText.toLowerCase();

							for (const item of menuItems) {
								if (item.textContent) {
									const itemTextLower = item.textContent.trim().toLowerCase();
									const itemValueLower = (item.getAttribute('data-value') || '').toLowerCase();

									// Match against both text and data-value (case-insensitive)
									if (itemTextLower === targetTextLower || itemValueLower === targetTextLower) {
										// Clear previous selections
										menuItems.forEach(mi => {
											mi.setAttribute('aria-selected', 'false');
											mi.classList.remove('selected');
										});

										// Select this item
										item.setAttribute('aria-selected', 'true');
										item.classList.add('selected');

										// Trigger click and change events
										item.click();
										const clickEvent = new MouseEvent('click', { view: window, bubbles: true, cancelable: true });
										item.dispatchEvent(clickEvent);

										return {
											success: true,
											message: `Selected ARIA menu item: ${item.textContent.trim()}`
										};
									}
								}
							}

							// Return available options as separate field
							const availableOptions = Array.from(menuItems).map(item => ({
								text: item.textContent ? item.textContent.trim() : '',
								value: item.getAttribute('data-value') || ''
							})).filter(opt => opt.text || opt.value);

							return {
								success: false,
								error: `Menu item with text or value '${targetText}' not found`,
								availableOptions: availableOptions
							};
						}

						// Handle Semantic UI or custom dropdowns
						if (element.classList.contains('dropdown') || element.classList.contains('ui')) {
							const menuItems = element.querySelectorAll('.item, .option, [data-value]');
							const targetTextLower = targetText.toLowerCase();

							for (const item of menuItems) {
								if (item.textContent) {
									const itemTextLower = item.textContent.trim().toLowerCase();
									const itemValueLower = (item.getAttribute('data-value') || '').toLowerCase();

									// Match against both text and data-value (case-insensitive)
									if (itemTextLower === targetTextLower || itemValueLower === targetTextLower) {
										// Clear previous selections
										menuItems.forEach(mi => {
											mi.classList.remove('selected', 'active');
										});

										// Select this item
										item.classList.add('selected', 'active');

										// Update dropdown text if there's a text element
										const textElement = element.querySelector('.text');
										if (textElement) {
											textElement.textContent = item.textContent.trim();
										}

										// Trigger click and change events
										item.click();
										const clickEvent = new MouseEvent('click', { view: window, bubbles: true, cancelable: true });
										item.dispatchEvent(clickEvent);

										// Also dispatch on the main dropdown element
										const dropdownChangeEvent = new Event('change', { bubbles: true });
										element.dispatchEvent(dropdownChangeEvent);

										return {
											success: true,
											message: `Selected custom dropdown item: ${item.textContent.trim()}`
										};
									}
								}
							}

							// Return available options as separate field
							const availableOptions = Array.from(menuItems).map(item => ({
								text: item.textContent ? item.textContent.trim() : '',
								value: item.getAttribute('data-value') || ''
							})).filter(opt => opt.text || opt.value);

							return {
								success: false,
								error: `Custom dropdown item with text or value '${targetText}' not found`,
								availableOptions: availableOptions
							};
						}

						return null; // Not a dropdown element
					}

					// Function to recursively search children for dropdowns
					function searchChildrenForSelection(element, maxDepth, currentDepth = 0) {
						if (currentDepth >= maxDepth) return null;

						// Check all direct children
						for (let child of element.children) {
							// Try selection on this child
							const result = attemptSelection(child);
							if (result && result.success) {
								return result;
							}

							// Recursively check this child's children
							const childResult = searchChildrenForSelection(child, maxDepth, currentDepth + 1);
							if (childResult && childResult.success) {
								return childResult;
							}
						}

						return null;
					}

					// First try the target element itself
					let selectionResult = attemptSelection(startElement);
					if (selectionResult) {
						// If attemptSelection returned a result (success or failure), use it
						// Don't search children if we found a dropdown element but selection failed
						return selectionResult;
					}

					// Only search children if target element is not a dropdown element
					selectionResult = searchChildrenForSelection(startElement, 4);
					if (selectionResult && selectionResult.success) {
						return selectionResult;
					}

					return {
						success: false,
						error: `Element and its children (depth 4) do not contain a dropdown with option '${targetText}' (tag: ${startElement.tagName}, role: ${startElement.getAttribute('role')}, classes: ${startElement.className})`
					};
				}
				"""

				result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
					params={
						'functionDeclaration': selection_script,
						'arguments': [{'value': target_text}],
						'objectId': object_id,
						'returnByValue': True,
					},
					session_id=cdp_session.session_id,
				)

				selection_result = result.get('result', {}).get('value', {})

				# If selection failed and all options are empty, the dropdown may be lazily populated.
				# Focus the element (triggers lazy loaders) and retry once after a wait.
				if not selection_result.get('success'):
					available_options = selection_result.get('availableOptions', [])
					all_empty = available_options and all(
						(not opt.get('text', '').strip() and not opt.get('value', '').strip())
						if isinstance(opt, dict)
						else not str(opt).strip()
						for opt in available_options
					)
					if all_empty:
						self.logger.info(
							'⚠️ All dropdown options are empty — options may be lazily loaded. Focusing element and retrying...'
						)

						# Use element.focus() only — no synthetic mouse events that leak isTrusted=false
						try:
							await cdp_session.cdp_client.send.Runtime.callFunctionOn(
								params={
									'functionDeclaration': 'function() { this.focus(); }',
									'objectId': object_id,
								},
								session_id=cdp_session.session_id,
							)
						except Exception:
							pass  # non-fatal, best-effort

						await asyncio.sleep(1.0)

						retry_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
							params={
								'functionDeclaration': selection_script,
								'arguments': [{'value': target_text}],
								'objectId': object_id,
								'returnByValue': True,
							},
							session_id=cdp_session.session_id,
						)
						selection_result = retry_result.get('result', {}).get('value', {})

				# Check if selection was reverted by framework - try clicking as fallback
				if selection_result.get('selectionReverted'):
					self.logger.info('⚠️ Selection was reverted by page framework, trying click fallback...')
					target_option = selection_result.get('targetOption', {})
					option_index = target_option.get('index', 0)

					# Try clicking on the option element directly
					click_fallback_script = """
					function(optionIndex) {
						const select = this;
						if (select.tagName.toLowerCase() !== 'select') return { success: false, error: 'Not a select element' };

						const option = select.options[optionIndex];
						if (!option) return { success: false, error: 'Option not found at index ' + optionIndex };

						// Method 1: Try using the native selectedIndex setter with a small delay
						const originalValue = select.value;

						// Simulate opening the dropdown (some frameworks need this)
						select.focus();
						const mouseDown = new MouseEvent('mousedown', { bubbles: true, cancelable: true, view: window });
						select.dispatchEvent(mouseDown);

						// Set using selectedIndex (more reliable for some frameworks)
						select.selectedIndex = optionIndex;

						// Click the option
						option.selected = true;
						const optionClick = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
						option.dispatchEvent(optionClick);

						// Close dropdown
						const mouseUp = new MouseEvent('mouseup', { bubbles: true, cancelable: true, view: window });
						select.dispatchEvent(mouseUp);

						// Fire change event
						const changeEvent = new Event('change', { bubbles: true, cancelable: true });
						select.dispatchEvent(changeEvent);

						// Blur to finalize
						select.blur();

						// Verify
						if (select.value === option.value || select.selectedIndex === optionIndex) {
							return {
								success: true,
								message: 'Selected via click fallback: ' + option.text.trim(),
								value: option.value
							};
						}

						return {
							success: false,
							error: 'Click fallback also failed - framework may block all programmatic selection',
							finalValue: select.value,
							expectedValue: option.value
						};
					}
					"""

					fallback_result = await cdp_session.cdp_client.send.Runtime.callFunctionOn(
						params={
							'functionDeclaration': click_fallback_script,
							'arguments': [{'value': option_index}],
							'objectId': object_id,
							'returnByValue': True,
						},
						session_id=cdp_session.session_id,
					)

					fallback_data = fallback_result.get('result', {}).get('value', {})
					if fallback_data.get('success'):
						msg = fallback_data.get('message', f'Selected option via click: {target_text}')
						self.logger.info(f'✅ {msg}')
						return {
							'success': 'true',
							'message': msg,
							'value': fallback_data.get('value', target_text),
							'backend_node_id': str(index_for_logging),
						}
					else:
						self.logger.warning(f'⚠️ Click fallback also failed: {fallback_data.get("error", "unknown")}')
						# Continue to error handling below

				if selection_result.get('success'):
					msg = selection_result.get('message', f'Selected option: {target_text}')
					self.logger.debug(f'{msg}')

					# Return the result as a dict
					return {
						'success': 'true',
						'message': msg,
						'value': selection_result.get('value', target_text),
						'backend_node_id': str(index_for_logging),
					}
				else:
					error_msg = selection_result.get('error', f'Failed to select option: {target_text}')
					available_options = selection_result.get('availableOptions', [])
					self.logger.error(f'❌ {error_msg}')
					self.logger.debug(f'Available options from JavaScript: {available_options}')

					# If we have available options, return structured error data
					if available_options:
						# Format options for short_term_memory (simple bulleted list)
						short_term_options = []
						for opt in available_options:
							if isinstance(opt, dict):
								text = opt.get('text', '').strip()
								value = opt.get('value', '').strip()
								if text:
									short_term_options.append(f'- {text}')
								elif value:
									short_term_options.append(f'- {value}')
							elif isinstance(opt, str):
								short_term_options.append(f'- {opt}')

						if short_term_options:
							short_term_memory = 'Available dropdown options  are:\n' + '\n'.join(short_term_options)
							long_term_memory = (
								f"Couldn't select the dropdown option as '{target_text}' is not one of the available options."
							)

							# Return error result with structured memory instead of raising exception
							return {
								'success': 'false',
								'error': error_msg,
								'short_term_memory': short_term_memory,
								'long_term_memory': long_term_memory,
								'backend_node_id': str(index_for_logging),
							}

					# Fallback to regular error result if no available options
					return {
						'success': 'false',
						'error': error_msg,
						'backend_node_id': str(index_for_logging),
					}

			except Exception as e:
				error_msg = f'Failed to select dropdown option: {str(e)}'
				self.logger.error(error_msg)
				raise ValueError(error_msg) from e

		except Exception as e:
			error_msg = f'Failed to select dropdown option "{target_text}" for element {index_for_logging}: {str(e)}'
			self.logger.error(error_msg)
			raise ValueError(error_msg) from e
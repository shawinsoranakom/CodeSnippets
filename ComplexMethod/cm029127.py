def _add_compound_components(self, simplified: SimplifiedNode, node: EnhancedDOMTreeNode) -> None:
		"""Enhance compound controls with information from their child components."""
		# Only process elements that might have compound components
		if node.tag_name not in ['input', 'select', 'details', 'audio', 'video']:
			return

		# For input elements, check for compound input types
		if node.tag_name == 'input':
			if not node.attributes or node.attributes.get('type') not in [
				'date',
				'time',
				'datetime-local',
				'month',
				'week',
				'range',
				'number',
				'color',
				'file',
			]:
				return
		# For other elements, check if they have AX child indicators
		elif not node.ax_node or not node.ax_node.child_ids:
			return

		# Add compound component information based on element type
		element_type = node.tag_name
		input_type = node.attributes.get('type', '') if node.attributes else ''

		if element_type == 'input':
			# NOTE: For date/time inputs, we DON'T add compound components because:
			# 1. They confuse the model (seeing "Day, Month, Year" suggests DD.MM.YYYY format)
			# 2. HTML5 date/time inputs ALWAYS require ISO format (YYYY-MM-DD, HH:MM, etc.)
			# 3. The placeholder attribute clearly shows the required format
			# 4. These inputs use direct value assignment, not sequential typing
			if input_type in ['date', 'time', 'datetime-local', 'month', 'week']:
				# Skip compound components for date/time inputs - format is shown in placeholder
				pass
			elif input_type == 'range':
				# Range slider with value indicator
				min_val = node.attributes.get('min', '0') if node.attributes else '0'
				max_val = node.attributes.get('max', '100') if node.attributes else '100'

				node._compound_children.append(
					{
						'role': 'slider',
						'name': 'Value',
						'valuemin': self._safe_parse_number(min_val, 0.0),
						'valuemax': self._safe_parse_number(max_val, 100.0),
						'valuenow': None,
					}
				)
				simplified.is_compound_component = True
			elif input_type == 'number':
				# Number input with increment/decrement buttons
				min_val = node.attributes.get('min') if node.attributes else None
				max_val = node.attributes.get('max') if node.attributes else None

				node._compound_children.extend(
					[
						{'role': 'button', 'name': 'Increment', 'valuemin': None, 'valuemax': None, 'valuenow': None},
						{'role': 'button', 'name': 'Decrement', 'valuemin': None, 'valuemax': None, 'valuenow': None},
						{
							'role': 'textbox',
							'name': 'Value',
							'valuemin': self._safe_parse_optional_number(min_val),
							'valuemax': self._safe_parse_optional_number(max_val),
							'valuenow': None,
						},
					]
				)
				simplified.is_compound_component = True
			elif input_type == 'color':
				# Color picker with components
				node._compound_children.extend(
					[
						{'role': 'textbox', 'name': 'Hex Value', 'valuemin': None, 'valuemax': None, 'valuenow': None},
						{'role': 'button', 'name': 'Color Picker', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					]
				)
				simplified.is_compound_component = True
			elif input_type == 'file':
				# File input with browse button
				multiple = 'multiple' in node.attributes if node.attributes else False

				# Extract current file selection state from AX tree
				current_value = 'None'  # Default to explicit "None" string for clarity
				if node.ax_node and node.ax_node.properties:
					for prop in node.ax_node.properties:
						# Try valuetext first (human-readable display like "file.pdf")
						if prop.name == 'valuetext' and prop.value:
							value_str = str(prop.value).strip()
							if value_str and value_str.lower() not in ['', 'no file chosen', 'no file selected']:
								current_value = value_str
							break
						# Also try 'value' property (may include full path)
						elif prop.name == 'value' and prop.value:
							value_str = str(prop.value).strip()
							if value_str:
								# For file inputs, value might be a full path - extract just filename
								if '\\' in value_str:
									current_value = value_str.split('\\')[-1]
								elif '/' in value_str:
									current_value = value_str.split('/')[-1]
								else:
									current_value = value_str
								break

				node._compound_children.extend(
					[
						{'role': 'button', 'name': 'Browse Files', 'valuemin': None, 'valuemax': None, 'valuenow': None},
						{
							'role': 'textbox',
							'name': f'{"Files" if multiple else "File"} Selected',
							'valuemin': None,
							'valuemax': None,
							'valuenow': current_value,  # Always shows state: filename or "None"
						},
					]
				)
				simplified.is_compound_component = True

		elif element_type == 'select':
			# Select dropdown with option list and detailed option information
			base_components = [
				{'role': 'button', 'name': 'Dropdown Toggle', 'valuemin': None, 'valuemax': None, 'valuenow': None}
			]

			# Extract option information from child nodes
			options_info = self._extract_select_options(node)
			if options_info:
				options_component = {
					'role': 'listbox',
					'name': 'Options',
					'valuemin': None,
					'valuemax': None,
					'valuenow': None,
					'options_count': options_info['count'],
					'first_options': options_info['first_options'],
				}
				if options_info['format_hint']:
					options_component['format_hint'] = options_info['format_hint']
				base_components.append(options_component)
			else:
				base_components.append(
					{'role': 'listbox', 'name': 'Options', 'valuemin': None, 'valuemax': None, 'valuenow': None}
				)

			node._compound_children.extend(base_components)
			simplified.is_compound_component = True

		elif element_type == 'details':
			# Details/summary disclosure widget
			node._compound_children.extend(
				[
					{'role': 'button', 'name': 'Toggle Disclosure', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					{'role': 'region', 'name': 'Content Area', 'valuemin': None, 'valuemax': None, 'valuenow': None},
				]
			)
			simplified.is_compound_component = True

		elif element_type == 'audio':
			# Audio player controls
			node._compound_children.extend(
				[
					{'role': 'button', 'name': 'Play/Pause', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					{'role': 'slider', 'name': 'Progress', 'valuemin': 0, 'valuemax': 100, 'valuenow': None},
					{'role': 'button', 'name': 'Mute', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					{'role': 'slider', 'name': 'Volume', 'valuemin': 0, 'valuemax': 100, 'valuenow': None},
				]
			)
			simplified.is_compound_component = True

		elif element_type == 'video':
			# Video player controls
			node._compound_children.extend(
				[
					{'role': 'button', 'name': 'Play/Pause', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					{'role': 'slider', 'name': 'Progress', 'valuemin': 0, 'valuemax': 100, 'valuenow': None},
					{'role': 'button', 'name': 'Mute', 'valuemin': None, 'valuemax': None, 'valuenow': None},
					{'role': 'slider', 'name': 'Volume', 'valuemin': 0, 'valuemax': 100, 'valuenow': None},
					{'role': 'button', 'name': 'Fullscreen', 'valuemin': None, 'valuemax': None, 'valuenow': None},
				]
			)
			simplified.is_compound_component = True
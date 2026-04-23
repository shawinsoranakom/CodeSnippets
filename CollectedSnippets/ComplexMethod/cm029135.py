def _build_attributes_string(node: EnhancedDOMTreeNode, include_attributes: list[str], text: str) -> str:
		"""Build the attributes string for an element."""
		attributes_to_include = {}

		# Include HTML attributes
		if node.attributes:
			attributes_to_include.update(
				{
					key: str(value).strip()
					for key, value in node.attributes.items()
					if key in include_attributes and str(value).strip() != ''
				}
			)

		# Add format hints for date/time inputs to help LLMs use the correct format
		# NOTE: These formats are standardized by HTML5 specification (ISO 8601), NOT locale-dependent
		# The browser may DISPLAY dates in locale format (MM/DD/YYYY in US, DD/MM/YYYY in EU),
		# but the .value attribute and programmatic setting ALWAYS uses these ISO formats:
		# - date: YYYY-MM-DD (e.g., "2024-03-15")
		# - time: HH:MM or HH:MM:SS (24-hour, e.g., "14:30")
		# - datetime-local: YYYY-MM-DDTHH:MM (e.g., "2024-03-15T14:30")
		# Reference: https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date
		if node.tag_name and node.tag_name.lower() == 'input' and node.attributes:
			input_type = node.attributes.get('type', '').lower()

			# For HTML5 date/time inputs, add a highly visible "format" attribute
			# This makes it IMPOSSIBLE for the model to miss the required format
			if input_type in ['date', 'time', 'datetime-local', 'month', 'week']:
				format_map = {
					'date': 'YYYY-MM-DD',
					'time': 'HH:MM',
					'datetime-local': 'YYYY-MM-DDTHH:MM',
					'month': 'YYYY-MM',
					'week': 'YYYY-W##',
				}
				# Add format as a special attribute that appears prominently
				# This appears BEFORE placeholder in the serialized output
				attributes_to_include['format'] = format_map[input_type]

			# Only add placeholder if it doesn't already exist
			if 'placeholder' in include_attributes and 'placeholder' not in attributes_to_include:
				# Native HTML5 date/time inputs - ISO format required
				if input_type == 'date':
					attributes_to_include['placeholder'] = 'YYYY-MM-DD'
				elif input_type == 'time':
					attributes_to_include['placeholder'] = 'HH:MM'
				elif input_type == 'datetime-local':
					attributes_to_include['placeholder'] = 'YYYY-MM-DDTHH:MM'
				elif input_type == 'month':
					attributes_to_include['placeholder'] = 'YYYY-MM'
				elif input_type == 'week':
					attributes_to_include['placeholder'] = 'YYYY-W##'
				# Tel - suggest format if no pattern attribute
				elif input_type == 'tel' and 'pattern' not in attributes_to_include:
					attributes_to_include['placeholder'] = '123-456-7890'
				# jQuery/Bootstrap/AngularJS datepickers (text inputs with datepicker classes/attributes)
				elif input_type in {'text', ''}:
					class_attr = node.attributes.get('class', '').lower()

					# Check for AngularJS UI Bootstrap datepicker (uib-datepicker-popup attribute)
					# This takes precedence as it's the most specific indicator
					if 'uib-datepicker-popup' in node.attributes:
						# Extract format from uib-datepicker-popup="MM/dd/yyyy"
						date_format = node.attributes.get('uib-datepicker-popup', '')
						if date_format:
							# Use 'expected_format' for clarity - this is the required input format
							attributes_to_include['expected_format'] = date_format
							# Also keep format for consistency with HTML5 date inputs
							attributes_to_include['format'] = date_format
					# Detect jQuery/Bootstrap datepickers by class names
					elif any(indicator in class_attr for indicator in ['datepicker', 'datetimepicker', 'daterangepicker']):
						# Try to get format from data-date-format attribute
						date_format = node.attributes.get('data-date-format', '')
						if date_format:
							attributes_to_include['placeholder'] = date_format
							attributes_to_include['format'] = date_format  # Also add format for jQuery datepickers
						else:
							# Default to common US format for jQuery datepickers
							attributes_to_include['placeholder'] = 'mm/dd/yyyy'
							attributes_to_include['format'] = 'mm/dd/yyyy'
					# Also detect by data-* attributes
					elif any(attr in node.attributes for attr in ['data-datepicker']):
						date_format = node.attributes.get('data-date-format', '')
						if date_format:
							attributes_to_include['placeholder'] = date_format
							attributes_to_include['format'] = date_format
						else:
							attributes_to_include['placeholder'] = 'mm/dd/yyyy'
							attributes_to_include['format'] = 'mm/dd/yyyy'

		# Never include values from password fields - they contain secrets that must not
		# leak into DOM snapshots sent to the LLM, where prompt injection could exfiltrate them.
		is_password_field = (
			node.tag_name
			and node.tag_name.lower() == 'input'
			and node.attributes
			and node.attributes.get('type', '').lower() == 'password'
		)

		# Include accessibility properties
		if node.ax_node and node.ax_node.properties:
			# Properties that carry field values - must be excluded for password fields
			value_properties = {'value', 'valuetext'}
			for prop in node.ax_node.properties:
				try:
					if prop.name in include_attributes and prop.value is not None:
						if is_password_field and prop.name in value_properties:
							continue
						# Convert boolean to lowercase string, keep others as-is
						if isinstance(prop.value, bool):
							attributes_to_include[prop.name] = str(prop.value).lower()
						else:
							prop_value_str = str(prop.value).strip()
							if prop_value_str:
								attributes_to_include[prop.name] = prop_value_str
				except (AttributeError, ValueError):
					continue

		# Special handling for form elements - ensure current value is shown
		# For text inputs, textareas, and selects, prioritize showing the current value from AX tree
		if node.tag_name and node.tag_name.lower() in ['input', 'textarea', 'select']:
			if is_password_field:
				attributes_to_include.pop('value', None)
			# ALWAYS check AX tree - it reflects actual typed value, DOM attribute may not update
			elif node.ax_node and node.ax_node.properties:
				for prop in node.ax_node.properties:
					# Try valuetext first (human-readable display value)
					if prop.name == 'valuetext' and prop.value:
						value_str = str(prop.value).strip()
						if value_str:
							attributes_to_include['value'] = value_str
							break
					# Also try 'value' property directly
					elif prop.name == 'value' and prop.value:
						value_str = str(prop.value).strip()
						if value_str:
							attributes_to_include['value'] = value_str
							break

		if not attributes_to_include:
			return ''

		# Remove duplicate values
		ordered_keys = [key for key in include_attributes if key in attributes_to_include]

		if len(ordered_keys) > 1:
			keys_to_remove = set()
			seen_values = {}

			# Attributes that should never be removed as duplicates (they serve distinct purposes)
			protected_attrs = {'format', 'expected_format', 'placeholder', 'value', 'aria-label', 'title'}

			for key in ordered_keys:
				value = attributes_to_include[key]
				if len(value) > 5:
					if value in seen_values and key not in protected_attrs:
						keys_to_remove.add(key)
					else:
						seen_values[value] = key

			for key in keys_to_remove:
				del attributes_to_include[key]

		# Remove attributes that duplicate accessibility data
		role = node.ax_node.role if node.ax_node else None
		if role and node.node_name == role:
			attributes_to_include.pop('role', None)

		# Remove type attribute if it matches the tag name (e.g. <button type="button">)
		if 'type' in attributes_to_include and attributes_to_include['type'].lower() == node.node_name.lower():
			del attributes_to_include['type']

		# Remove invalid attribute if it's false (only show when true)
		if 'invalid' in attributes_to_include and attributes_to_include['invalid'].lower() == 'false':
			del attributes_to_include['invalid']

		boolean_attrs = {'required'}
		for attr in boolean_attrs:
			if attr in attributes_to_include and attributes_to_include[attr].lower() in {'false', '0', 'no'}:
				del attributes_to_include[attr]

		# Remove aria-expanded if we have expanded (prefer AX tree over HTML attribute)
		if 'expanded' in attributes_to_include and 'aria-expanded' in attributes_to_include:
			del attributes_to_include['aria-expanded']

		attrs_to_remove_if_text_matches = ['aria-label', 'placeholder', 'title']
		for attr in attrs_to_remove_if_text_matches:
			if attributes_to_include.get(attr) and attributes_to_include.get(attr, '').strip().lower() == text.strip().lower():
				del attributes_to_include[attr]

		if attributes_to_include:
			# Format attributes, wrapping empty values in quotes for clarity
			formatted_attrs = []
			for key, value in attributes_to_include.items():
				capped_value = cap_text_length(value, 100)
				# Show empty values as key='' instead of key=
				if not capped_value:
					formatted_attrs.append(f"{key}=''")
				else:
					formatted_attrs.append(f'{key}={capped_value}')
			return ' '.join(formatted_attrs)

		return ''
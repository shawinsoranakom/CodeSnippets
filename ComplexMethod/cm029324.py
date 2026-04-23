def _requires_direct_value_assignment(self, element_node: EnhancedDOMTreeNode) -> bool:
		"""
		Check if an element requires direct value assignment instead of character-by-character typing.

		Certain input types have compound components, custom plugins, or special requirements
		that make character-by-character typing unreliable. These need direct .value assignment:

		Native HTML5:
		- date, time, datetime-local: Have spinbutton components (ISO format required)
		- month, week: Similar compound structure
		- color: Expects hex format #RRGGBB
		- range: Needs numeric value within min/max

		jQuery/Bootstrap Datepickers:
		- Detected by class names or data attributes
		- Often expect specific date formats (MM/DD/YYYY, DD/MM/YYYY, etc.)

		Note: We use direct assignment because:
		1. Typing triggers intermediate validation that might reject partial values
		2. Compound components (like date spinbuttons) don't work with sequential typing
		3. It's much faster and more reliable
		4. We dispatch proper input/change events afterward to trigger listeners
		"""
		if not element_node.tag_name or not element_node.attributes:
			return False

		tag_name = element_node.tag_name.lower()

		# Check for native HTML5 inputs that need direct assignment
		if tag_name == 'input':
			input_type = element_node.attributes.get('type', '').lower()

			# Native HTML5 inputs with compound components or strict formats
			if input_type in {'date', 'time', 'datetime-local', 'month', 'week', 'color', 'range'}:
				return True

			# Detect jQuery/Bootstrap datepickers (text inputs with datepicker plugins)
			if input_type in {'text', ''}:
				# Check for common datepicker indicators
				class_attr = element_node.attributes.get('class', '').lower()
				if any(
					indicator in class_attr
					for indicator in ['datepicker', 'daterangepicker', 'datetimepicker', 'bootstrap-datepicker']
				):
					return True

				# Check for data attributes indicating datepickers
				if any(attr in element_node.attributes for attr in ['data-datepicker', 'data-date-format', 'data-provide']):
					return True

		return False
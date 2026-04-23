def detect_variables_in_history(history: AgentHistoryList) -> dict[str, DetectedVariable]:
	"""
	Analyze agent history and detect reusable variables.

	Uses two strategies:
	1. Element attributes (id, name, type, placeholder, aria-label) - most reliable
	2. Value pattern matching (email, phone, date formats) - fallback

	Returns:
		Dictionary mapping variable names to DetectedVariable objects
	"""
	detected: dict[str, DetectedVariable] = {}
	detected_values: set[str] = set()  # Track which values we've already detected

	for step_idx, history_item in enumerate(history.history):
		if not history_item.model_output:
			continue

		for action_idx, action in enumerate(history_item.model_output.action):
			# Convert action to dict - handle both Pydantic models and dict-like objects
			if hasattr(action, 'model_dump'):
				action_dict = action.model_dump()
			elif isinstance(action, dict):
				action_dict = action
			else:
				# For SimpleNamespace or similar objects
				action_dict = vars(action)

			# Get the interacted element for this action (if available)
			element = None
			if history_item.state and history_item.state.interacted_element:
				if len(history_item.state.interacted_element) > action_idx:
					element = history_item.state.interacted_element[action_idx]

			# Detect variables in this action
			_detect_in_action(action_dict, element, detected, detected_values)

	return detected